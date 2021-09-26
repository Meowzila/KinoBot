import grequests
from bs4 import BeautifulSoup
import re
import requests
from pymongo import MongoClient
import time

# Connect to MongoDB
client = MongoClient('localhost', 27017)
db = client['KinoBotDB']

genres = ['action', 'adventure', 'animation', 'comedy', 'crime', 'documentary', 'drama', 'family', 'fantasy',
          'history',
          'horror', 'music', 'mystery', 'romance', 'science-fiction', 'thriller', 'tv-movie', 'war', 'western']


# Returns the number of pages of watched films for a given user (if any)
def GetPageNum(username):
    user_page = BeautifulSoup(requests.get(f'https://letterboxd.com/{username.lower()}/films/').text, 'lxml')
    try:
        page_num = user_page.find('div', class_='paginate-pages').text.split()[-1:]
    except AttributeError:
        page_num = [1]
    return int(page_num[0])


# Returns list containing relevant film info
def FindAllFilmInfo(film_page_html, film_page_genres_html):
    try:
        film_info = [film_page_html.find('h1', class_='headline-1 js-widont prettify').text,  # name
                     film_page_html.find('a', class_='').text,  # year
                     film_page_html.find('span', class_='prettify').text,  # director
                     re.findall(r'"ratingValue":(.+?),', str(film_page_html.find_all()))[0],  # rating
                     film_page_html.find('p', class_='text-link text-footer').text.split()[0],  # length
                     re.findall(r'"/actor/([\w-]+)/"',
                                str(film_page_html.find('div', class_='cast-list text-sluglist'))),  # actors
                     film_page_html.find('img', class_='image').get("src"),  # banner
                     film_page_genres_html.find('div', class_='text-sluglist capitalize').text.split()]  # genres
        return film_info
    except AttributeError:
        pass


# Runs asynchronous http requests for every film url and returns all film information
def CreateUrlsAndRatings(pages, username, process=True):
    page_urls, film_urls, user_rating = [], [], []
    if pages > 1:
        for page in range(1, pages + 1):
            page_urls.append(f'https://letterboxd.com/{username.lower()}/films/by/member-rating/page/{str(page)}')
        page_reqs = (grequests.get(link) for link in page_urls)
        page_responses = grequests.map(page_reqs)
        for r in page_responses:
            film_page = BeautifulSoup(r.text, 'lxml')
            film_urls += re.findall(r'data-film-slug="/film/([\w-]+)/"', str(film_page.find(
                'ul', class_='poster-list -p70 -grid film-list clear')))
            user_rating += re.findall(r'([★½]+)', str(film_page.find_all('span')))

        film_urls = TrimUrlRating(film_urls, user_rating)
        if process is True:
            user_rating = CreateRatingDictList(user_rating, username.lower())
            existing_urls, new_urls, existing_ratings, new_ratings = SplitUrlsAndRatings(film_urls, user_rating)
            return existing_urls, new_urls, existing_ratings, new_ratings, user_rating
        return film_urls, user_rating
    else:
        user_film_page = requests.get(f'https://letterboxd.com/{username.lower()}/films/by/member-rating/').text
        film_page = BeautifulSoup(user_film_page, 'lxml')
        film_urls = re.findall(r'data-film-slug="/film/([\w-]+)/"', str(film_page.find(
            'ul', class_='poster-list -p70 -grid film-list clear')))
        user_rating += re.findall(r'([★½]+)', str(film_page.find_all('span')))

        film_urls = TrimUrlRating(film_urls, user_rating)
        if process is True:
            user_rating = CreateRatingDictList(user_rating, username.lower())
            existing_urls, new_urls, existing_ratings, new_ratings = SplitUrlsAndRatings(film_urls, user_rating)
            return existing_urls, new_urls, existing_ratings, new_ratings, user_rating
        return film_urls, user_rating


# Trims films listed as "watched" but not rated by user from film_urls
def TrimUrlRating(film_urls, film_ratings):
    if len(film_urls) != len(film_ratings):
        del film_urls[-(len(film_urls) - len(film_ratings)):]
    return film_urls


# Convert rating from "★★★★★" format to float
def CreateRatingDictList(film_ratings, username):
    rating_dict = {
        "½": 0.5, "★": 1.0, "★½": 1.5, "★★": 2.0,
        "★★½": 2.5, "★★★": 3.0, "★★★½": 3.5,
        "★★★★": 4.0, "★★★★½": 4.5, "★★★★★": 5.0
    }
    watch_list = []
    for rating in film_ratings:
        if rating in rating_dict:
            watch_list.append({username: rating_dict[rating]})
    return watch_list


# Prints cache progress
def Progress(progress, film_urls_len):
    if progress == film_urls_len // 4:
        return '...25% complete'
    elif progress == film_urls_len // 2:
        return '...50% complete'
    elif progress == int(film_urls_len * 0.75):
        return '...75% complete'
    elif film_urls_len / progress == 1:
        return '...100% complete!'
    else:
        return None


# Returns list of lists containing all relevant film information
def ScrapeFilmPage(film_urls):
    complete_film_info = []
    counter = 0
    film_reqs = (grequests.get(f'https://letterboxd.com/film/{url}') for url in film_urls)
    film_responses = grequests.map(film_reqs)
    for r in film_responses:
        film_page = BeautifulSoup(r.text, 'lxml')
        film_page_genres = BeautifulSoup(r.text, 'lxml')
        complete_film_info.append(FindAllFilmInfo(film_page, film_page_genres))
        counter += 1
        progress = Progress(counter, len(film_responses))
        if progress is not None:
            print(progress)
    return complete_film_info


# Splits film data and associated rating into new lists for later processing
def SplitUrlsAndRatings(film_urls, film_ratings):
    cursor = db['Films']
    existing_urls, new_urls, existing_ratings, new_ratings = [], [], [], []
    for film in range(len(film_urls)):
        if cursor.find_one({"film_url": film_urls[film]}):
            existing_urls.append(film_urls[film])
            existing_ratings.append(film_ratings[film])
        else:
            new_urls.append(film_urls[film])
            new_ratings.append(film_ratings[film])
    return existing_urls, new_urls, existing_ratings, new_ratings


# Checks whether a user's film rating is already present in MongoDB and inserts if not
def MongoDBChecker(film_urls, film_ratings):
    cursor = db['Films']
    for film in range(len(film_urls)):
        url_result = cursor.find_one({"film_url": film_urls[film]})
        if film_ratings[film] in url_result['user_ratings']:
            pass
        else:
            cursor.update_one({'film_url': film_urls[film]},
                              {'$push': {'user_ratings': film_ratings[film]}}, upsert=True)


# Inserts all relevant information for NEW film entries only
def MongoDBInserter(film_info, new_film_urls, new_film_ratings):
    cursor = db['Films']
    try:
        for film in range(len(new_film_urls)):
            cursor.insert_many([{'film_url': str(new_film_urls[film]),
                                 'film_name': str(film_info[film][0]),
                                 'year': str(film_info[film][1]),
                                 'director': str(film_info[film][2]),
                                 'weighted_average': float(film_info[film][3]),
                                 'length': int(film_info[film][4].replace(",", "")),
                                 'cast': film_info[film][5],
                                 'banner': str(film_info[film][6]),
                                 'genres': film_info[film][7],
                                 'user_ratings': [new_film_ratings[film]]
                                 }])
    except TypeError:
        pass


def FastGetGenrePageNum(username):
    genre_pages = []
    genre_reqs = (grequests.get(
        f'https://letterboxd.com/{username.lower()}/films/genre/{genre}/by/member-rating/') for genre in genres)
    genre_responses = grequests.map(genre_reqs)
    for r in genre_responses:
        genre_page = BeautifulSoup(r.text, 'lxml')
        try:
            page_num = genre_page.find('div', class_='paginate-pages').text.split()[-1:]
            genre_pages.append(int(page_num[0]))
        except AttributeError:
            genre_pages.append(1)
    return genre_pages


def ConvertGenreListToDict(genre_pages):
    genre_dict = {}
    for genre in range(len(genres)):
        genre_dict.update({genres[genre]: genre_pages[genre]})
    return genre_dict


def ConvertRatingToFloat(genre_ratings):
    conv_ratings = []
    for rating in range(len(genre_ratings)):
        if "½" in genre_ratings[rating]:
            conv_ratings.append(len(genre_ratings[rating]) - 0.5)
        else:
            conv_ratings.append(len(genre_ratings[rating]))
    try:
        return (sum(conv_ratings) / len(conv_ratings)).__round__(2), len(conv_ratings)
    except ZeroDivisionError:
        return 0, 0


def GenreCreateUrlsAndRatings(genre_pages, username):
    genre_score_dict, num_genres = {}, {}
    for genre in genres:
        if genre_pages.get(genre) > 1:
            genre_urls, user_rating = [], []
            for page in range(1, genre_pages.get(genre) + 1):
                genre_urls.append(
                    f'https://letterboxd.com/{username.lower()}/films/genre/{genre}/by/member-rating/page/{page}')
            page_reqs = (grequests.get(link) for link in genre_urls)
            page_responses = grequests.map(page_reqs)
            for r in page_responses:
                film_page = BeautifulSoup(r.text, 'lxml')
                user_rating += re.findall(r'([★½]+)', str(film_page.find_all('span')))
            genre_rating, num_genre = ConvertRatingToFloat(user_rating)
            num_genres.update({genre: num_genre})
            genre_score_dict.update({genre: genre_rating})
        else:
            user_rating = []
            user_film_page = requests.get(
                f'https://letterboxd.com/{username.lower()}/films/genre/{genre}/by/member-rating/').text
            film_page = BeautifulSoup(user_film_page, 'lxml')
            user_rating += re.findall(r'([★½]+)', str(film_page.find_all('span')))
            genre_rating, num_genre = ConvertRatingToFloat(user_rating)
            num_genres.update({genre: num_genre})
            genre_score_dict.update({genre: genre_rating})
    return genre_score_dict, num_genres
