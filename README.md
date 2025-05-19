A FinTech API I created over a couple days to showcase secure API development. Written in Flask and using postgresql in a docker container. 

Requires docker and docker-compose

run `docker-compose up -d` then after installing requirements.txt `python3 init_db.py` to initialize the database.

run `python3 main.py` Flask uses port 5000 by default when running its built in development server.

Navigate to http://localhost:5000/apidocs/ to access the swaggerUI
