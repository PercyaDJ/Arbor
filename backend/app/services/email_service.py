"""
ARBOR - Service de notifications email.
Envoi d'alertes et de digests aux utilisateurs.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Template
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.alert import Alert
from app.models.bom import Component
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.models.vulnerability import Vulnerability


# --- Templates email HTML ---

ALERT_TEMPLATE = Template("""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Inter', sans-serif; background: #0a0f0d; color: #e8f0ec; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background: #131a16; border-radius: 12px; padding: 24px; border: 1px solid #243029;">
    <h1 style="color: #4ade80; font-size: 20px; margin-bottom: 8px;">🌳 ARBOR — Nouvelle alerte</h1>
    <hr style="border-color: #243029; margin: 16px 0;">

    <table style="width: 100%; border-collapse: collapse;">
      <tr>
        <td style="padding: 8px 0; color: #94a89d;">Projet</td>
        <td style="padding: 8px 0; font-weight: 600;">{{ project_name }}</td>
      </tr>
      <tr>
        <td style="padding: 8px 0; color: #94a89d;">CVE</td>
        <td style="padding: 8px 0; font-weight: 600;">{{ cve_id }}</td>
      </tr>
      <tr>
        <td style="padding: 8px 0; color: #94a89d;">Composant</td>
        <td style="padding: 8px 0;">{{ component_name }}@{{ component_version }}</td>
      </tr>
      <tr>
        <td style="padding: 8px 0; color: #94a89d;">Sévérité</td>
        <td style="padding: 8px 0;">
          <span style="background: {{ severity_color }}; color: #0a0f0d; padding: 2px 10px; border-radius: 4px; font-weight: 600; font-size: 13px;">
            {{ severity }}
          </span>
        </td>
      </tr>
      <tr>
        <td style="padding: 8px 0; color: #94a89d;">CVSS</td>
        <td style="padding: 8px 0;">{{ cvss_score or 'N/A' }}</td>
      </tr>
    </table>

    <div style="margin-top: 16px; padding: 12px; background: #1a2420; border-radius: 8px; font-size: 14px; color: #94a89d;">
      {{ description[:300] }}{% if description|length > 300 %}...{% endif %}
    </div>

    <div style="margin-top: 20px; text-align: center;">
      <a href="{{ arbor_url }}" style="display: inline-block; background: #4ade80; color: #0a0f0d; padding: 10px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">
        Voir dans ARBOR
      </a>
    </div>

    <p style="margin-top: 20px; font-size: 12px; color: #5f7368; text-align: center;">
      ARBOR — Automated Risk & Bill Of Materials Registry
    </p>
  </div>
</body>
</html>
""")

SEVERITY_COLORS = {
    "critical": "#ef4444",
    "high": "#f97316",
    "medium": "#eab308",
    "low": "#3b82f6",
    "info": "#6b7280",
}


def send_alert_email(
    db: Session,
    alert: Alert,
) -> int:
    """
    Envoie un email d'alerte aux membres du projet concerné.
    Respecte les préférences de notification (seuil CVSS).
    Retourne le nombre d'emails envoyés.
    """
    # Charger les données liées
    project = db.query(Project).filter(Project.id == alert.project_id).first()
    vulnerability = db.query(Vulnerability).filter(Vulnerability.id == alert.vulnerability_id).first()
    component = db.query(Component).filter(Component.id == alert.component_id).first()

    if not project or not vulnerability or not component:
        return 0

    # Trouver les membres à notifier
    members = (
        db.query(ProjectMember, User)
        .join(User, ProjectMember.user_id == User.id)
        .filter(ProjectMember.project_id == alert.project_id, User.is_active.is_(True))
        .all()
    )

    sent_count = 0
    for membership, user in members:
        # Vérifier les préférences de notification
        prefs = user.notification_preferences or {}
        min_cvss = prefs.get("cvss_min_threshold", 0.0)
        digest_mode = prefs.get("digest_mode", "realtime")

        score = vulnerability.cvss_v3_score or vulnerability.cvss_v2_score or 0.0
        if score < min_cvss:
            continue

        if digest_mode != "realtime":
            continue  # Les digests seront envoyés par la tâche dédiée

        # Construire et envoyer l'email
        severity = vulnerability.severity.value
        html = ALERT_TEMPLATE.render(
            project_name=project.name,
            cve_id=vulnerability.cve_id,
            component_name=component.name,
            component_version=component.version,
            severity=severity.upper(),
            severity_color=SEVERITY_COLORS.get(severity, "#6b7280"),
            cvss_score=vulnerability.cvss_v3_score,
            description=vulnerability.description or "",
            arbor_url=f"/projects/{project.id}",
        )

        success = _send_email(
            to_email=user.email,
            subject=f"[ARBOR] {severity.upper()} — {vulnerability.cve_id} dans {project.name}",
            html_body=html,
        )
        if success:
            sent_count += 1

    return sent_count


def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Envoie un email via SMTP. Retourne True si succès."""
    settings = get_settings()

    if not settings.smtp_host or settings.smtp_host == "localhost":
        print(f"[EMAIL] SMTP non configuré — email simulé pour {to_email}: {subject}")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        if settings.smtp_tls:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)

        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)

        server.sendmail(settings.smtp_from, [to_email], msg.as_string())
        server.quit()
        return True

    except Exception as e:
        print(f"[EMAIL] Erreur d'envoi vers {to_email}: {e}")
        return False
