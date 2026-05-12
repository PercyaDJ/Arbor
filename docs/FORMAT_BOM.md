# Guide des Formats de BOM (Bill of Materials) pour ARBOR

Le registre ARBOR est conçu pour importer, analyser et surveiller les dépendances de vos projets. Pour ce faire, ARBOR accepte plusieurs formats standards de l'industrie, ainsi qu'un format CSV simplifié.

## 1. Formats Standards Supportés

ARBOR utilise en interne la spécification **CycloneDX**. Il est fortement recommandé d'utiliser des outils de génération automatiques qui produisent ces formats dans le cadre de vos pipelines CI/CD.

### CycloneDX (Recommandé)
- **Extensions acceptées** : `.json`, `.xml`
- **Versions supportées** : 1.4, 1.5
- **Outils de génération recommandés** :
  - NPM/NodeJS : `@cyclonedx/cyclonedx-npm`
  - Python : `cyclonedx-bom`
  - Maven/Java : `cyclonedx-maven-plugin`
  - Go : `cyclonedx-gomod`

### SPDX (Software Package Data Exchange)
- **Extensions acceptées** : `.json`, `.spdx`
- **Versions supportées** : 2.2, 2.3
- **Note** : Les fichiers SPDX sont automatiquement convertis au format interne ARBOR lors de l'import.

## 2. Format Manuel : CSV (Valeurs Séparées par des Virgules)

Pour les projets ne disposant pas d'outils de génération automatique, ARBOR permet l'import de BOMs au format **CSV**. Ce format doit respecter une structure stricte.

### Structure du fichier CSV
Le fichier doit contenir des en-têtes exacts sur la première ligne (sensible à la casse).

| Colonne | Requis | Description | Exemple |
| :--- | :--- | :--- | :--- |
| `name` | Oui | Nom du composant ou de la dépendance | `react`, `requests`, `log4j` |
| `version` | Oui | Version exacte de la dépendance | `18.2.0`, `2.31.0` |
| `type` | Non | Type du composant (défaut: `library`) | `library`, `framework`, `os` |
| `group` | Non | Espace de nom ou groupe (ex: Maven ou NPM) | `org.apache.logging.log4j` |
| `purl` | Non* | Package URL (identifiant unique standard) | `pkg:pypi/requests@2.31.0` |
| `license` | Non | Identifiant de licence SPDX | `MIT`, `Apache-2.0` |

*Note sur le champ `purl` : S'il est vide, ARBOR tentera de le générer automatiquement à partir de `type`, `group`, `name`, et `version` pour surveiller les vulnérabilités. Il est recommandé de fournir un PURL exact si possible.*

### Exemple de fichier `bom.csv`
```csv
name,version,type,group,purl,license
requests,2.31.0,library,,pkg:pypi/requests@2.31.0,Apache-2.0
react,18.2.0,library,,pkg:npm/react@18.2.0,MIT
log4j-core,2.14.1,library,org.apache.logging.log4j,pkg:maven/org.apache.logging.log4j/log4j-core@2.14.1,Apache-2.0
```

## 3. Bonnes Pratiques d'Organisation

Pour tirer le meilleur parti d'ARBOR, nous vous recommandons l'organisation suivante :

1. **Un Projet ARBOR par Dépôt Git / Application** : Ne mélangez pas les dépendances de plusieurs applications distinctes dans un seul projet ARBOR, sauf s'il s'agit d'un monorepo étroitement couplé.
2. **Nommage des Composants** : Soyez le plus précis possible. Utilisez l'écosystème exact dans le PURL (ex: `pkg:npm/...`, `pkg:pypi/...`, `pkg:maven/...`).
3. **Mises à jour automatisées** : Configurez votre intégration continue (CI/CD) pour pousser un nouveau fichier BOM vers l'API d'ARBOR (via l'endpoint `/api/v1/projects/{id}/bom`) à chaque _release_ ou chaque fusion sur la branche principale.
