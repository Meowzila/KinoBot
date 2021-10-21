# KinoBot
KinoBot is a Discord chat bot written in python with various movie related features

KinoBot uses BeautifulSoup4 to scrape letterboxd.com and rottentomatoes.com for movie-related information and store the info in a local MongoDB database

Command Output Examples:

films (user) : returns number of films (on letterboxd) a user has watched YTD and in total
![alt text](https://i.imgur.com/u85vsXG.png)


recent (user) : returns embed of most recently watched film (on letterboxd) for user containing movie banner and user rating
![alt text](https://i.imgur.com/kPyWqlI.png)


fruit (movie) : returns rottentomatoes specific information on a particular movie
![alt text](https://i.imgur.com/yCnifmq.png)


average (user) : calculates average rating of all rated films for user (on letterboxd)
![alt text](https://i.imgur.com/Ac7kyX7.png)


cache (user) : caches user films to mongodb along with movie information such as name, banner, year, director, etc
Checks local db for both user entries AND film entries

![alt text](https://i.imgur.com/0sduPhl.png)


taste (user) : calculates two things:
1. Average user rating distance from letterboxd film rating
2. Critical index (How much more positively/negatively a user tends to rate their films compared to the average letterboxd film rating)
![alt text](https://i.imgur.com/k62rgUU.png)


genres (user) : calculates average rating for each genre of film watched by user
![alt text](https://i.imgur.com/uQ2QfuE.png)
