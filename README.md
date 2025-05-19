A FinTech API I created over a couple days to showcase secure API development. Written in Flask and using postgresql in a docker container. 

Requires docker and docker-compose

run `docker-compose up -d` then after installing requirements.txt `python3 init_db.py` to initialize the database.

run `python3 main.py` Flask uses port 5000 by default when running its built in development server.

Navigate to http://localhost:5000/apidocs/ to access the swaggerUI


TODO:    

     Token revocation / blacklist support

     MFA

     KYC status enforcement (e.g., preventing unverified users from transferring funds)

     IP address logging & anomaly detection (critical for fraud prevention)

     Encrypted storage for sensitive PII at rest

     HTTPS-only enforcement

     Security headers (CSP, HSTS, etc. via Flask middleware)

     Rate limiting / abuse prevention (Flask-Limiter or API gateway enforcement)

     Audit logging of sensitive actions (transfers, logins, failed attempts)

     Automatic account locking after X failed login attempts

     Celery/Task queue for async operations (sending verification email)

     Email verification logic

     Unit & integration tests

     Health checks & observability

     Monitoring, alerting, and metrics (Prometheus/Grafana)

     Add a CI/CD pipeline with tests

     Containerize the whole thing

     Add error monitoring (Sentry) and infra security (OWASP headers)
