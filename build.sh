# For Windows users: Run the 6 command lines in build.sh file individually in terminal.

docker build -t brendankhow/carpark:1.0 -f carpark.Dockerfile ./
docker build -t brendankhow/favourites:1.0 -f favourites.Dockerfile ./
docker build -t brendankhow/geocode:1.0 -f geocode.Dockerfile ./
docker build -t brendankhow/getcarpark:1.0 -f getcarpark.Dockerfile ./
docker build -t brendankhow/notification:1.0 -f notification.Dockerfile ./
docker build -t brendankhow/users:1.0 -f users.Dockerfile ./