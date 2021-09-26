import discord
from discord.ext import commands
from kino_functions import *

# Connect to MongoDB
client = MongoClient('localhost', 27017)
db = client['KinoBotDB']


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
        start = time.perf_counter()

        old_urls, new_urls, old_ratings, new_ratings, user_ratings = \
            CreateUrlsAndRatings(GetPageNum(user), user)
        new_scraped_info = ScrapeFilmPage(new_urls)
        MongoDBInserter(new_scraped_info, new_urls, new_ratings)
        MongoDBChecker(old_urls, old_ratings)

        fin = (time.perf_counter() - start).__round__(2)
        await ctx.send(f'{len(new_urls)} entries cached from {user.lower()} in {fin}s!')

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
                f'Avg Distance from Letterboxd: {(total_absolute_difference / len(film_name_urls)).__round__(3)}\n'
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
                f'Avg Distance from Letterboxd: {(total_absolute_difference / len(film_name_urls)).__round__(3)}\n'
                f'Critical Index: {(critical_difference / len(film_name_urls)).__round__(3)}')

    @commands.command(name='genres')
    async def genres(self, ctx, user):
        start = time.perf_counter()
        genre_dict, genre_num_dict = GenreCreateUrlsAndRatings(ConvertGenreListToDict(FastGetGenrePageNum(user)), user)
        fin = (time.perf_counter() - start).__round__(2)
        print(f'\n{fin}s')
        kino_embed = discord.Embed(title=f'{user.title()}\'s Genre Ratings')
        for genre in genres:
            kino_embed.add_field(name=f'{genre.title()}',
                                 value=f'{genre_dict.get(genre)} (Total Films: {genre_num_dict.get(genre)})')
        kino_embed.set_footer(text="All information obtained from Letterboxd.com")
        await ctx.send(embed=kino_embed)


def setup(bot):
    bot.add_cog(Kino(bot))
