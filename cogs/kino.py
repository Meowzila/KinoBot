import requests
import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import re
from pymongo import MongoClient
from operator import itemgetter

# Connect to MongoDB
client = MongoClient('localhost', 27017)
db = client['film_database']


class Kino(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='films',
                      brief='Displays film stats (Letterboxd)',
                      description='Displays number of films watched in total and YTD',
                      category='Kino')
    async def films(self, ctx, user=None):
        if user is None:
            await ctx.send('Please enter a valid username')
            return
        try:
            html_text = requests.get('https://letterboxd.com/' + str(user)).text
            soup = BeautifulSoup(html_text, 'lxml')
            main_page = soup.find('div', class_='profile-stats js-profile-stats').text
            filtered = re.sub(r'[^0-9]', ' ', main_page).split()
            await ctx.send(f'{user} has watched {filtered[0]} films, {filtered[1]} of which have been in 2021.')
        except AttributeError:
            await ctx.send('User does not exist!')

    @commands.command(name='recent',
                      brief='Displays most recently watched film (Letterboxd)',
                      description='Displays embed of most recently watched film, rating, and movie banner',
                      category='Kino')
    async def recent(self, ctx, user=None):
        if user is None:
            await ctx.send('Please enter a valid username')
            return
        try:
            html_text = requests.get('https://letterboxd.com/' + str(user)).text
            soup = BeautifulSoup(html_text, 'lxml')
            recent_activity = soup.find(id='recent-activity')
            film_name = recent_activity.find('div').get("data-film-slug").replace("/film/", "").replace("/",
                                                                                                        "").replace("-",
                                                                                                                    " ")
            rating = soup.find('p', class_='poster-viewingdata').text.split()
            film_url = "https://letterboxd.com/film/" + film_name.lower().replace(" ", "-").replace("'", "")
            image_req = requests.get(film_url).text
            image_soup = BeautifulSoup(image_req, 'lxml')
            image = image_soup.find('img', class_='image').get("src")
            correct_name = image_soup.find('h1', class_='headline-1 js-widont prettify').text

            kino_embed = discord.Embed(title=f'{correct_name} ({user})')
            kino_embed.set_image(url=image)
            kino_embed.add_field(name=f"Rating: ", value=rating[0])
            kino_embed.add_field(name="URL:", value=film_url, inline=False)
            kino_embed.set_footer(text="All information obtained by Letterboxd.com")
            await ctx.send(embed=kino_embed)
        except AttributeError:
            await ctx.send('User does not exist!')

    @commands.command(name='fruit',
                      brief='Shows film information ratings from RottenTomatoes',
                      category='Kino')
    async def fruit(self, ctx, *, movie=None):
        if movie is None:
            await ctx.send('Please enter a valid movie title!')
            return
        try:
            html_text = requests.get(
                'https://www.rottentomatoes.com/m/' + str(movie).replace(" ", "_").replace("'", "").replace(":",
                                                                                                            "")).text
            soup = BeautifulSoup(html_text, 'lxml')
            red_fruit = soup.find('div', class_='thumbnail-scoreboard-wrap')
            tomatometer = red_fruit.find('score-board', class_='scoreboard').get("tomatometerscore")
            audiencescore = red_fruit.find('score-board', class_='scoreboard').get("audiencescore")
            tomatometer_state = red_fruit.find('score-board', class_='scoreboard').get("tomatometerstate")
            audience_state = red_fruit.find('score-board', class_='scoreboard').get("audiencestate")
            banner = red_fruit.find('img', class_='posterImage js-lazyLoad').get("data-src")
            if tomatometer_state == "certified-fresh":
                tomato_ico = ":sparkling_heart:"
            elif tomatometer_state == "fresh":
                tomato_ico = ":tomato:"
            else:
                tomato_ico = ":nauseated_face:"
            if audience_state == "upright":
                audience_ico = ":popcorn:"
            else:
                audience_ico = ":thumbsdown:"
            kino_embed = discord.Embed(title=f'{movie.title()}')
            kino_embed.set_image(url=banner)
            kino_embed.add_field(name=f"Tomatometer: ", value=tomato_ico + tomatometer + "%")
            kino_embed.add_field(name=f"Audience Score: ", value=audience_ico + audiencescore + "%")
            kino_embed.add_field(name="URL:", value='https://www.rottentomatoes.com/m/' + str(
                movie).replace(" ", "_").replace("'", "").replace(":", ""), inline=False)
            kino_embed.set_footer(text="All information obtained from Rottentomatoes.com")
            await ctx.send(embed=kino_embed)
        except AttributeError:
            await ctx.send('Movie does not exist!')

    @commands.command(name='compare',
                      brief='Compares film stats of two users (Letterboxd)',
                      description='Compares film stats and displays whether User 1 has watched more/fewer films than User 2',
                      category='Kino')
    async def compare(self, ctx, user1=None, user2=None):
        if user1 is None or user2 is None:
            await ctx.send('Please enter two valid usernames!')
            return
        try:
            html_text1 = requests.get('https://letterboxd.com/' + str(user1)).text
            html_text2 = requests.get('https://letterboxd.com/' + str(user2)).text
            soup1 = BeautifulSoup(html_text1, 'lxml')
            soup2 = BeautifulSoup(html_text2, 'lxml')
            pf_stats1 = soup1.find('div', class_='profile-stats js-profile-stats').text
            pf_stats2 = soup2.find('div', class_='profile-stats js-profile-stats').text
            filtered_stats1 = re.sub(r'[^0-9]', ' ', pf_stats1).split()
            filtered_stats2 = re.sub(r'[^0-9]', ' ', pf_stats2).split()
            if int(filtered_stats1[0]) > int(filtered_stats2[0]):
                await ctx.send(
                    f'{user1} has watched {int(filtered_stats1[0]) - int(filtered_stats2[0])} more films than {user2}.')
            else:
                await ctx.send(
                    f'{user1} has watched {int(filtered_stats2[0]) - int(filtered_stats1[0])} fewer films than {user2}.')
        except AttributeError:
            await ctx.send('At least one user does not exist!')

    @commands.command(name='average')
    async def average(self, ctx, user):
        html_text = requests.get('https://letterboxd.com/' + str(user) + "/films/").text
        soup = BeautifulSoup(html_text, 'lxml')
        try:
            num_pages = soup.find('div', class_='paginate-pages').text.split()[-1:]
        except AttributeError:
            num_pages = [1]
        total_watched = soup.find('ul', class_='sub-nav')
        num_films = int(re.sub(r'[^0-9]', '', total_watched.find('a', class_='tooltip').get("title")))
        stars, fragments = 0, 0

        if int(num_pages[0]) > 1:
            for page in range(1, int(num_pages[0]) + 1):
                new_html = requests.get('https://letterboxd.com/' + str(user) + "/films/page/" + str(page)).text
                new_soup = BeautifulSoup(new_html, 'lxml')
                film_grid = new_soup.find('ul', class_='poster-list -p70 -grid film-list clear')
                rating = re.sub(r'[^★½]', '', str(film_grid.find_all('p')))
                for thing in rating:
                    if thing == "★":
                        stars += 1
                    else:
                        fragments += 1
            total_rating = ((stars + (fragments / 2)) / num_films)
            await ctx.send(f'{user}\'s Average Film Rating on Letterboxd: {total_rating.__round__(2)}/5.00')
        else:
            for page in range(num_pages[0]):
                film_grid = soup.find('ul', class_='poster-list -p70 -grid film-list clear')
                rating = re.sub(r'[^★½]', '', str(film_grid.find_all('p')))
                for thing in rating:
                    if thing == "★":
                        stars += 1
                    else:
                        fragments += 1
            total_rating = ((stars + (fragments / 2)) / num_films)
            await ctx.send(f'{user}\'s Average Film Rating on Letterboxd: {total_rating.__round__(2)}/5.00')

    @commands.command(name='cache')
    async def cache(self, ctx, user):
        cursor = db['Films']
        film_name_urls = []
        new_entries, progress = 0, 0
        html_text = requests.get('https://letterboxd.com/' + str(user) + "/films/").text
        soup = BeautifulSoup(html_text, 'lxml')
        try:
            num_pages = soup.find('div', class_='paginate-pages').text.split()[-1:]
        except AttributeError:
            num_pages = [1]

        if int(num_pages[0]) > 1:
            # Add all films into list film_name_urls (For users with multiple pages of films)
            for page in range(1, int(num_pages[0]) + 1):
                new_html = requests.get('https://letterboxd.com/' + str(user) + "/films/page/" + str(page)).text
                new_soup = BeautifulSoup(new_html, 'lxml')
                film_name_urls += re.findall(r'data-film-slug="/film/([\w-]+)/"', str(new_soup.find(
                    'ul', class_='poster-list -p70 -grid film-list clear')))
            print(f'Pages to be cached: {num_pages[0]}\n'
                  f'Number of films to be cached: {len(film_name_urls)}')
            # Loops through each film in film_name_urls
            for film_url in film_name_urls:
                # Cache progress updates
                progress += 1
                if progress == int(len(film_name_urls) / 4):
                    await ctx.send(f'...25% complete')
                elif progress == int(len(film_name_urls) / 2):
                    await ctx.send(f'...50% complete')
                elif progress == int(len(film_name_urls) * 0.75):
                    await ctx.send(f'...75% complete')
                elif (len(film_name_urls) / progress) == 1:
                    await ctx.send(f'100% complete!')
                # Checks whether the film exists in database
                result = cursor.find_one({"film_url_name": str(film_url)})
                # If there IS a match in database
                if result is not None:
                    # Check whether the user's rating exists in database'
                    try:
                        list(map(itemgetter(user), list(result['watched_by'])))
                        print(f'{user} WAS found in {result["watched_by"]}')
                        pass
                    # User has NOT watched the film but it DOES exist in database
                    except KeyError:
                        # Request html to grab user film rating
                        watched_html = requests.get(
                            'https://letterboxd.com/' + user + '/film/' + film_url + '/activity/').text
                        watch_soup = BeautifulSoup(watched_html, 'lxml')
                        conv_user_rating = 0
                        user_rating = re.findall(r'([★½]+)', str(watch_soup.find_all('span')))
                        try:
                            # Convert rating from "★★★★★" format to float
                            for char in str(user_rating[0]):
                                if char == "½":
                                    conv_user_rating += 0.5
                                else:
                                    conv_user_rating += 1
                            watched_by = {user: conv_user_rating}
                            # If user rating does not exist in database, ADD IT
                            if list(watched_by)[0] not in list(result["watched_by"]):
                                cursor.update_one({'film_url_name': film_url}, {'$push': {'watched_by': watched_by}})
                        except IndexError:
                            print('Film not rated by user')
                            pass
                    print(f'Found db match: {film_url}\n')
                    pass
                else:
                    # Grabbing all necessary info to insert into database as new entry
                    print(f'No match found for: {film_url}, adding new entry to db...')
                    film_page_html = requests.get('https://letterboxd.com/film/' + film_url).text
                    info_soup = BeautifulSoup(film_page_html, 'lxml')
                    film_name = info_soup.find('h1', class_='headline-1 js-widont prettify').text
                    film_year = info_soup.find('a', class_='').text
                    film_director = info_soup.find('span', class_='prettify').text
                    film_average_score = re.findall(r'"ratingValue":(.+?),', str(info_soup.find_all()))[0]
                    film_length = info_soup.find('p', class_='text-link text-footer').text.split()[0]
                    film_cast = re.findall(r'"/actor/([\w-]+)/"',
                                           str(info_soup.find('div', class_='cast-list text-sluglist')))
                    banner = info_soup.find('img', class_='image').get("src")
                    genre_html = requests.get('https://letterboxd.com/film/' + film_url + "/genres/").text
                    genre_soup = BeautifulSoup(genre_html, 'lxml')
                    film_genres = genre_soup.find('div', class_='text-sluglist capitalize').text.split()
                    conv_user_rating = 0
                    # Request html to grab user film rating
                    watched_html = requests.get(
                        'https://letterboxd.com/' + user + '/film/' + film_url + '/activity/').text
                    watch_soup = BeautifulSoup(watched_html, 'lxml')
                    user_rating = re.findall(r'([★½]+)', str(watch_soup.find_all('span')))
                    try:
                        # Convert rating from "★★★★★" format to float
                        for char in str(user_rating[0]):
                            if char == "½":
                                conv_user_rating += 0.5
                            else:
                                conv_user_rating += 1
                        watched_by = [{user: conv_user_rating}]
                        cursor.insert_many([{'film_url_name': str(film_url),
                                             'film_name': str(film_name),
                                             'banner': banner,
                                             'year': int(film_year),
                                             'director': str(film_director),
                                             'weighted_average': float(film_average_score),
                                             'length': int(film_length.replace(",", "")),
                                             'cast': film_cast,
                                             'genres': film_genres,
                                             'watched_by': watched_by}])
                        new_entries += 1
                    except IndexError:
                        print('Film not rated by user')
                        pass
            await ctx.send(f'{new_entries} new entries cached from {user}!')
        else:
            # Add all films into list film_name_urls (For users with ONE page of films)
            for page in range(num_pages[0]):
                film_name_urls += re.findall(r'data-film-slug="/film/([\w-]+)/"', str(soup.find(
                    'ul', class_='poster-list -p70 -grid film-list clear')))
            print(f'Pages to be cached: {num_pages[0]}\n'
                  f'Number of films to be cached: {len(film_name_urls)}')
            # Loops through each film in film_name_urls
            for film_url in film_name_urls:
                # Cache progress updates
                progress += 1
                if progress == int(len(film_name_urls) / 4):
                    await ctx.send(f'...25% complete')
                elif progress == int(len(film_name_urls) / 2):
                    await ctx.send(f'...50% complete')
                elif progress == int(len(film_name_urls) * 0.75):
                    await ctx.send(f'...75% complete')
                elif (len(film_name_urls) / progress) == 1:
                    await ctx.send(f'100% complete!')
                # Checks whether the film exists in database
                result = cursor.find_one({"film_url_name": str(film_url)})
                # If there IS a match in database
                if result is not None:
                    # Check whether the user has watched the film
                    try:
                        list(map(itemgetter(user), list(result['watched_by'])))
                        print(f'{user} WAS found in {result["watched_by"]}')
                        pass
                    # User has NOT watched the film but it DOES exist in database
                    except KeyError:
                        # Request html to grab user film rating
                        watched_html = requests.get(
                            'https://letterboxd.com/' + user + '/film/' + film_url + '/activity/').text
                        watch_soup = BeautifulSoup(watched_html, 'lxml')
                        conv_user_rating = 0
                        user_rating = re.findall(r'([★½]+)', str(watch_soup.find_all('span')))
                        try:
                            # Convert rating from "★★★★★" format to float
                            for char in str(user_rating[0]):
                                if char == "½":
                                    conv_user_rating += 0.5
                                else:
                                    conv_user_rating += 1
                            watched_by = {user: conv_user_rating}
                            # If user rating does not exist in database, ADD IT
                            if list(watched_by)[0] not in list(result["watched_by"]):
                                cursor.update_one({'film_url_name': film_url}, {'$push': {'watched_by': watched_by}})
                        except IndexError:
                            print('Film not rated by user')
                            pass
                    print(f'Found db match: {film_url}\n')
                    pass
                # Film does not exist in database
                else:
                    # Grabbing all necessary info to insert into database as new entry
                    print(f'No match found for: {film_url}, adding new entry to db...')
                    film_page_html = requests.get('https://letterboxd.com/film/' + film_url).text
                    info_soup = BeautifulSoup(film_page_html, 'lxml')
                    film_name = info_soup.find('h1', class_='headline-1 js-widont prettify').text
                    film_year = info_soup.find('a', class_='').text
                    film_director = info_soup.find('span', class_='prettify').text
                    film_average_score = re.findall(r'"ratingValue":(.+?),', str(info_soup.find_all()))[0]
                    film_length = info_soup.find('p', class_='text-link text-footer').text.split()[0]
                    film_cast = re.findall(r'"/actor/([\w-]+)/"',
                                           str(info_soup.find('div', class_='cast-list text-sluglist')))
                    banner = info_soup.find('img', class_='image').get("src")
                    genre_html = requests.get('https://letterboxd.com/film/' + film_url + "/genres/").text
                    genre_soup = BeautifulSoup(genre_html, 'lxml')
                    film_genres = genre_soup.find('div', class_='text-sluglist capitalize').text.split()
                    conv_user_rating = 0
                    # Request html to grab user film rating
                    watched_html = requests.get(
                        'https://letterboxd.com/' + user + '/film/' + film_url + '/activity/').text
                    watch_soup = BeautifulSoup(watched_html, 'lxml')
                    user_rating = re.findall(r'([★½]+)', str(watch_soup.find_all('span')))
                    try:
                        # Convert rating from "★★★★★" format to float
                        for char in str(user_rating[0]):
                            if char == "½":
                                conv_user_rating += 0.5
                            else:
                                conv_user_rating += 1
                        watched_by = [{user: conv_user_rating}]
                        cursor.insert_many([{'film_url_name': str(film_url),
                                             'film_name': str(film_name),
                                             'banner': banner,
                                             'year': int(film_year),
                                             'director': str(film_director),
                                             'weighted_average': float(film_average_score),
                                             'length': int(film_length.replace(",", "")),
                                             'cast': film_cast,
                                             'genres': film_genres,
                                             'watched_by': watched_by}])
                        new_entries += 1
                    except IndexError:
                        print('Film not rated by user')
                        pass
            await ctx.send(f'{new_entries} new entries cached from {user}!')

    @commands.command(name='taste')
    async def taste(self, ctx, user):
        cursor = db['Films']
        html_text = requests.get('https://letterboxd.com/' + str(user) + "/films/by/member-rating/").text
        soup = BeautifulSoup(html_text, 'lxml')

        try:
            num_pages = soup.find('div', class_='paginate-pages').text.split()[-1:]
        except AttributeError:
            num_pages = [1]

        total_absolute_difference, critical_difference = 0, 0
        film_name_urls = []
        if int(num_pages[0]) > 1:
            user_ratings, conv_ratings = [], []
            for page in range(1, int(num_pages[0]) + 1):
                new_html = requests.get(
                    'https://letterboxd.com/' + str(user) + "/films/by/member-rating/page/" + str(page)).text
                new_soup = BeautifulSoup(new_html, 'lxml')
                film_name_urls += re.findall(r'data-film-slug="/film/([\w-]+)/"', str(new_soup.find(
                    'ul', class_='poster-list -p70 -grid film-list clear')))
                user_ratings += re.findall(r'([★½]+)',
                                           str(new_soup.find('ul', class_='poster-list -p70 -grid film-list clear')))
                if len(film_name_urls) == 0:
                    await ctx.send(f'{user} does not exist!')
                    return
            for rating in range(len(user_ratings)):
                if "½" in user_ratings[rating]:
                    conv_ratings.append(len(user_ratings[rating]) - 0.5)
                else:
                    conv_ratings.append(len(user_ratings[rating]))
            for _ in range(len(film_name_urls) - len(conv_ratings)):
                film_name_urls.pop()
            for film in range(len(film_name_urls)):
                result = cursor.find_one({"film_url_name": str(film_name_urls[film])})
                try:
                    total_absolute_difference += abs(float(conv_ratings[film]) - float(result["weighted_average"]))
                    critical_difference += float(conv_ratings[film]) - float(result["weighted_average"])
                except TypeError:
                    await ctx.send(f'{user}\'s films are not cached, please use !cache {user}')
            await ctx.send(
                f'Average Distance from Letterboxd Rating: {(total_absolute_difference / len(film_name_urls)).__round__(3)}\n'
                f'Critical Index: {(critical_difference / len(film_name_urls)).__round__(3)}')

        else:
            conv_ratings = []
            for page in range(num_pages[0]):
                film_name_urls += re.findall(r'data-film-slug="/film/([\w-]+)/"', str(soup.find(
                    'ul', class_='poster-list -p70 -grid film-list clear')))
            user_ratings = re.findall(r'([★½]+)', str(soup.find('ul', class_='poster-list -p70 -grid film-list clear')))
            if len(film_name_urls) == 0:
                await ctx.send(f'{user} does not exist!')
                return
            for rating in range(len(user_ratings)):
                if "½" in user_ratings[rating]:
                    conv_ratings.append(len(user_ratings[rating]) - 0.5)
                else:
                    conv_ratings.append(len(user_ratings[rating]))
            for _ in range(len(film_name_urls) - len(conv_ratings)):
                film_name_urls.pop()
            for film in range(len(film_name_urls)):
                result = cursor.find_one({"film_url_name": str(film_name_urls[film])})
                try:
                    total_absolute_difference += abs(float(conv_ratings[film]) - float(result["weighted_average"]))
                    critical_difference += float(conv_ratings[film]) - float(result["weighted_average"])
                except TypeError:
                    await ctx.send(f'{user}\'s films are not cached, please use !cache {user}')
            await ctx.send(
                f'Average Distance from Letterboxd Rating: {(total_absolute_difference / len(film_name_urls)).__round__(3)}\n'
                f'Critical Index: {(critical_difference / len(film_name_urls)).__round__(3)}')

    @commands.command(name='genres')
    async def genres(self, ctx, user):
        genres = ['action', 'adventure', 'animation', 'comedy', 'crime', 'documentary', 'drama', 'family', 'fantasy',
                  'history',
                  'horror', 'music', 'mystery', 'romance', 'science-fiction', 'thriller', 'tv-movie', 'war', 'western']
        genre_ratings, num_films = [], []
        for genre in genres:
            html_text = requests.get(
                'https://letterboxd.com/' + str(user) + "/films/genre/" + genre + "/by/member-rating/").text
            soup = BeautifulSoup(html_text, 'lxml')

            try:
                num_pages = soup.find('div', class_='paginate-pages').text.split()[-1:]
            except AttributeError:
                num_pages = [1]

            if int(num_pages[0]) > 1:
                user_ratings, conv_ratings = [], []
                for page in range(1, int(num_pages[0]) + 1):
                    new_html = requests.get(
                        'https://letterboxd.com/' + str(
                            user) + "/films/genre/" + genre + "/by/member-rating/page/" + str(page)).text
                    new_soup = BeautifulSoup(new_html, 'lxml')
                    user_ratings += re.findall(r'([★½]+)',
                                               str(new_soup.find('ul',
                                                                 class_='poster-list -p70 -grid film-list clear')))
                    for rating in range(len(user_ratings)):
                        if "½" in user_ratings[rating]:
                            conv_ratings.append(len(user_ratings[rating]) - 0.5)
                        else:
                            conv_ratings.append(len(user_ratings[rating]))
                if len(conv_ratings) == 0:
                    genre_ratings.append(0)
                    num_films.append(0)
                else:
                    genre_ratings.append((sum(conv_ratings) / len(conv_ratings)).__round__(2))
                    num_films.append(re.findall(r'([\d]+)', str(soup.find('h2', class_='ui-block-heading')))[1])
            else:
                conv_ratings = []
                user_ratings = re.findall(r'([★½]+)',
                                          str(soup.find('ul', class_='poster-list -p70 -grid film-list clear')))
                for rating in range(len(user_ratings)):
                    if "½" in user_ratings[rating]:
                        conv_ratings.append(len(user_ratings[rating]) - 0.5)
                    else:
                        conv_ratings.append(len(user_ratings[rating]))
                if len(conv_ratings) == 0:
                    genre_ratings.append(0)
                    num_films.append(0)
                else:
                    genre_ratings.append((sum(conv_ratings) / len(conv_ratings)).__round__(2))
                    num_films.append(re.findall(r'([\d]+)', str(soup.find('h2', class_='ui-block-heading')))[1])
        kino_embed = discord.Embed(title=f'Average Ratings for each Genre')
        for rating in range(len(genre_ratings)):
            kino_embed.add_field(name=f'{genres[rating].title()}',
                                 value=f'{genre_ratings[rating]} (Total Films: {num_films[rating]})')
        kino_embed.set_footer(text="All information obtained from Letterboxd.com")
        await ctx.send(embed=kino_embed)


def setup(bot):
    bot.add_cog(Kino(bot))
