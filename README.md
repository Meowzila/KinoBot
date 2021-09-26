# KinoBot
Discord bot written in python with various movie related features

Uses BeautifulSoup4 to scrape letterboxd.com and rottentomatoes.com for movie-related information.
Stores information in local MongoDB database

Commands (prefix = "!")

films (user) : returns number of films (on letterboxd) a user has watched YTD and in total

recent (user) : returns embed of most recently watched film (on letterboxd) for user containing movie banner and user rating

fruit (movie) : returns rottentomatoes specific information on a particular movie

average (user) : calculates average rating of all rated films for user (on letterboxd)

cache (user) : caches all watched films of user to mongodb along with movie information such as name, banner, year, director, cast, average score, genres, etc

taste (user) : compares user rating of every film watched by user to average score (on letterboxd) and calculates average overall distance away from letterboxd average

genres (user) : calculates average rating for each genre of film watched by user
