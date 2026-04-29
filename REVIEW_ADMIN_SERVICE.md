# Review complete de `admin_service/`

Date de revue : 2026-04-29  
Etat revu : implementation courante de `admin_service/`, integration avec `user_service`, `worker_service`, Postgres content/identity, Redis, Qdrant et synchronisation du catalogue RSS.

## Synthese executive

`admin_service` est un service interne plus riche qu'il n'en a l'air depuis son `README`. Il sert de facade d'administration, orchestre plusieurs workflows RSS, delegue des operations a `user_service` et `worker_service`, et expose un endpoint de health detaille couvrant Postgres, Redis et Qdrant.

Le socle est globalement correct :

- Auth inter-services obligatoire hors local, avec comparaison constant-time.
- Separation des acces content DB / identity DB.
- Liveness simple via `/internal/health` et health detaille via `/internal/admin/health/`.
- Lock applicatif autour des operations RSS critiques.
- SQL parametre dans les clients DB lus pendant cette revue.
- Structure FastAPI lisible avec routers fins et services dedies.

Verdict : le service est exploitable comme brique interne, mais il reste plusieurs risques avant exposition a un trafic d'administration reel. Les plus importants concernent la couverture de tests, la reproductibilite des integrations inter-services, quelques fragilites de securite/configuration, et la robustesse operationnelle du pipeline RSS.

## Ce qui est bien

- `main.py` garde un bootstrap assez net et centralise.
- Les appels vers `user_service` et `worker_service` sont encapsules dans des clients dedies.
- Le endpoint `/internal/admin/health/` verifie reellement les dependances techniques au lieu de renvoyer un simple `ok`.
- La resolution des `DATABASE_URL` refuse les valeurs implicites en environnement production-like si `REQUIRE_EXPLICIT_DATABASE_URLS` n'est pas desactive.
- Les operations RSS sensibles utilisent `job_lock`, ce qui reduit le risque de doubles synchronisations concurrentes.
- Les routes admin bornent correctement plusieurs parametres d'entree avec `Query` et `Path`.
- Le service evite de melanger la logique HTTP avec les workflows RSS les plus lourds.

## Findings prioritaires

### Eleve - Couverture de tests quasiment inexistante au niveau comportemental

Le service n'a qu'un test de compilation de sources dans `admin_service/tests/test_source_syntax.py`.

Impact : aucune verification automatique ne protege les chemins critiques suivants :

- auth inter-service ;
- health detaillee ;
- delegation vers `user_service` et `worker_service` ;
- sync RSS avec lock, git et persistance SQL ;
- toggles `enabled` feeds/companies ;
- erreurs Qdrant, Redis et upstream HTTP.

Recommandation :

- Ajouter des tests unitaires sur `app/internal/security.py`, `app/clients/networking/service_http_client.py` et les services RSS.
- Ajouter au moins une suite d'integration sur `/internal/admin/*` avec dependances mockees.
- Ajouter une suite DB pour `sync_rss_catalog`, toggles RSS et `read_admin_stats`.

### Eleve - `APP_ENV` peut desactiver l'auth inter-service meme si le mode strict est demande

La logique de `admin_service/app/internal/security.py` traite `APP_ENV=dev|local|test` comme prioritaire. Si cette variable est mal renseignee, le service bypassera l'auth inter-service meme si l'intention de deploiement etait stricte.

Impact : un deploiement mal configure peut accepter des appels internes non authentifies.

Recommandation :

- Faire primer explicitement `REQUIRE_INTERNAL_SERVICE_TOKEN=true` sur `APP_ENV`.
- Ajouter des tests couvrant `APP_ENV=dev` combine a `REQUIRE_INTERNAL_SERVICE_TOKEN=true`.
- Injecter explicitement `APP_ENV=production` ou `staging` dans les environnements non locaux.

### Eleve - Contrats inter-services locaux, dupliques et non verifies

`admin_service` consomme `user_service` et `worker_service` via des schemas locaux dans `app/schemas/*` et des clients HTTP ad hoc, au lieu de s'appuyer sur une dependance partagee versionnee comme `auth_service` le fait avec `shared_backend`.

Impact : un drift de contrat entre services peut casser les appels admin sans signal avant integration. Le risque est reel pour :

- `AdminUserRead`, `AdminUserListRead`, `AdminUserUpdateRequestSchema` ;
- `WorkerServiceStatsRead` ;
- schemas jobs / automation / enqueue.

Recommandation :

- Mutualiser les schemas inter-services vraiment partages dans `shared_backend` ou un package commun versionne.
- Ajouter des tests de contrat minimaux entre `admin_service`, `user_service` et `worker_service`.
- Documenter la procedure de changement de schema inter-service.

### Moyen/Eleve - Pipeline RSS sensible aux pannes externes et peu teste bout en bout

`admin_service/app/rss/services/rss_sync_service.py` combine synchronisation Git, parsing JSON, reconciliation SQL et commit transactionnel dans un meme workflow.

Impact : la fonctionnalite est puissante mais concentre plusieurs points de panne :

- indisponibilite Git distante ;
- payload JSON invalide ;
- divergence entre revision Git et etat DB ;
- erreurs de nettoyage company/feed pendant le reconcile.

Le code traite correctement le rollback et persiste un etat d'echec si possible, mais sans test d'integration cette chaine reste fragile.

Recommandation :

- Ajouter un test d'integration DB + faux repo Git couvrant `clone -> sync -> noop -> update -> failure`.
- Verifier les cas de suppression de feeds et companies devenues obsoletes.
- Ajouter des metrics ou logs structures par phase du sync.

### Moyen - Client Redis maison non atomique pour les operations a TTL

`admin_service/app/clients/networking/redis_networking_client.py` fait `INCR` puis `EXPIRE` seulement si le compteur vaut `1`.

Impact : si `INCR` reussit et `EXPIRE` echoue, la cle peut rester sans TTL. Le risque est rare mais connu sur ce pattern.

Recommandation :

- Remplacer `INCR` + `EXPIRE` par un script Lua atomique si cette primitive est reutilisee pour du controle de flux important.
- Ajouter un test unitaire du comportement TTL.

### Moyen - Health detaillee utile, mais observabilite encore faible

Le endpoint `/internal/admin/health/` remonte bien l'etat de Postgres, Redis et Qdrant, mais le service manque encore de logs structures et de metrics metier.

Impact : en incident, il sera difficile de distinguer :

- echec upstream `user_service` ;
- echec upstream `worker_service` ;
- panne Qdrant ;
- panne Redis ;
- erreur Git lors du sync RSS ;
- contention sur les locks RSS.

Recommandation :

- Ajouter logs structures avec correlation id.
- Ajouter compteurs sur appels upstream, sync RSS, locks refuses, toggles et jobs admin.
- Ajouter mesures de latence sur `user_service` et `worker_service`.

### Moyen - Route `rss_public_router` definie mais non branchee

`admin_service/app/rss/rss_router.py` declare `rss_public_router`, mais `admin_service/main.py` n'inclut que `rss_admin_router`.

Impact : la route existe dans le code mais pas dans l'application. Cela cree de la confusion documentaire et du code mort potentiel.

Recommandation :

- Soit supprimer `rss_public_router` si elle ne doit pas exister dans ce service.
- Soit l'inclure explicitement si c'est un comportement voulu.
- Ajouter un test de routing pour les endpoints RSS exposes.

### Moyen - Image Docker et execution runtime encore perfectibles

Le `Dockerfile` utilise `python:3.11-slim`, installe `git` dans l'image runtime et execute le process par defaut en root.

Impact : surface d'image plus large et hardening incomplet pour un service d'administration.

Recommandation :

- Passer a un utilisateur non-root.
- Evaluer un build multi-stage.
- Limiter `git` a l'image/build strictement necessaire si possible.

## Securite detaillee

### Inter-service

Bon :

- Header dedie `x-manifeed-internal-token`.
- Comparaison avec `secrets.compare_digest`.
- Refus d'un token trop court hors local.

Reste a faire :

- Corriger la priorite `APP_ENV` vs `REQUIRE_INTERNAL_SERVICE_TOKEN`.
- Ajouter des tests de non-regression sur la matrice de configuration.

### Surface HTTP

Bon :

- Les routers `/internal/admin/*` sont proteges par `Depends(require_internal_service_token)`.
- Les parametres les plus evidents sont bornes.

Reste a faire :

- Ajouter des tests d'auth sur toutes les familles de routes.
- Verifier si CORS/CSRF doivent vraiment rester actifs sur un service strictement interne.

### Operations RSS

Bon :

- Lock applicatif autour des operations d'ecriture.
- Validation Pydantic du catalogue JSON.
- Rollback explicite en cas d'erreur de sync.

Reste a faire :

- Ajouter des tests sur les suppressions et les cas d'erreur Git/JSON/DB.
- Ajouter des garde-fous d'observabilite.

## Architecture

L'architecture est globalement coherente :

- `app/routers`, `app/internal`, `app/analytics` pour l'exposition HTTP ;
- `app/services` et `app/rss/services` pour les cas d'usage ;
- `app/clients/networking` pour les appels externes ;
- `app/rss/database` et `app/sources/database` pour l'acces SQL ;
- `database.py` pour les engines et sessions.

Le decoupage est lisible, mais deux tendances sont a surveiller :

- duplication de schemas inter-services dans plusieurs repos ;
- concentration progressive de logique dans le domaine RSS, qui devient le coeur complexe du service.

## Contrats API actuels

Routes principales observees :

- `GET /internal/health` : liveness simple.
- `GET /internal/admin/health/` : health detaillee content DB, identity DB, Qdrant, Redis.
- `GET /internal/admin/stats` : stats admin agregees + workers connectes.
- `GET/PATCH /internal/admin/users...` : delegation vers `user_service`.
- `GET/POST/PATCH /internal/admin/jobs...` : delegation vers `worker_service`.
- `GET/PATCH/POST /internal/admin/rss...` : catalogue RSS, toggles et sync.
- `GET /internal/admin/analysis/*` : overview et similar sources.

## Tests et verification

Verifications executees pendant cette revue :

- `python3 -m compileall -q admin_service` : OK.
- Lecture des points d'entree, services critiques, clients HTTP, securite inter-service, health, RSS sync, Qdrant et Redis.

Limites de verification :

- `pytest` n'est pas installe dans l'environnement courant, donc la suite de tests n'a pas pu etre executee ici.
- Les dependances Python de runtime comme `fastapi` ne sont pas installees dans cet environnement, donc un import applicatif complet n'a pas pu etre verifie.
- Pas de test d'integration avec Postgres, Redis, Qdrant, `user_service` ou `worker_service`.

## Plan d'action recommande

### P0 - Avant usage admin intensif

- Ajouter des tests comportementaux sur auth interne, health, delegation HTTP et RSS sync.
- Faire primer `REQUIRE_INTERNAL_SERVICE_TOKEN=true` sur `APP_ENV`.
- Ajouter des tests de contrat inter-services ou mutualiser les schemas partages.

### P1 - Stabilisation

- Ajouter logs structures et metrics sur appels upstream, sync RSS, locks et erreurs externes.
- Clarifier ou supprimer `rss_public_router`.
- Durcir l'image Docker et l'execution runtime.

### P2 - Long terme

- Extraire les contrats inter-services vers une dependance partagee versionnee.
- Renforcer le pipeline RSS avec davantage de tests d'integration et de garde-fous operationnels.
