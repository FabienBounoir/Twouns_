import os
from dotenv import load_dotenv

import re
import tweepy
import numpy as np
import matplotlib.pyplot as plt
import json
import shutil


from PIL import Image
from datetime import datetime, timedelta
from scipy.ndimage import gaussian_gradient_magnitude
from wordcloud import WordCloud, ImageColorGenerator


def nextDayList():
    print("📝 Update l'ordre des channels")

    # mettre la liste à la fin de la liste
    with open("channelGP.json", "r") as f:
        liste_arrays = json.load(f)

    # Récupérer la première array et la supprimer de la liste
    premiere_array = liste_arrays.pop(0)

    # Ajouter la première array à la fin de la liste
    liste_arrays.append(premiere_array)

    # Ouvrir le fichier en mode écriture et écrire la liste mise à jour
    with open("channelGP.json", "w") as f:
        json.dump(liste_arrays, f)


# load env variables
print("🔄 Load env variables")
load_dotenv()

# Twitter API credentials
consumer_key = os.getenv("API_KEY")
consumer_secret = os.getenv("API_SECRET_KEY")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

# Authentification

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
apiOld = tweepy.API(auth)

api = tweepy.Client(access_token=access_token,
                    access_token_secret=access_token_secret,
                    consumer_key=consumer_key,
                    consumer_secret=consumer_secret)

print("🔓 Authentification Twitter")

# Date du jour
date = datetime.now()
dateFormated = date.strftime("%d-%m-%Y_%H:%M:%S")

# get the channel order
with open('channelGP.json', 'r') as f:
    data = json.load(f)


# extraire la liste du jour
channels_of_the_day = data[0]

# check if array is empty
if not channels_of_the_day:
    print("❌ No channel found for this date")
    nextDayList()
    exit()


d = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()

print("🎆 Generate Image for this channels:")
print(channels_of_the_day)

with open('customTweetGp.json') as f:
    sentences = json.load(f)

for channel_name in channels_of_the_day:
    print("_________________________________________________________")

    twitter_name = ""

    print("🌌 Generate Image for " + channel_name + " chat...")

    # load chat transcript text file
    try:
        text = open(
            os.path.join(d, "./../tchat/" + channel_name + ".txt"), encoding="utf-8"
        ).read()
    except:
        print("❌ No chat transcript found for " + channel_name)
        continue

    logo_path = os.path.join(d, "./../logoChannel/")
    logo_files = os.listdir(logo_path)

    file_logo = ""

    for logo_file in logo_files:
        if logo_file.find(channel_name) != -1:
            twitter_name = logo_file.split("-")[1].split(".")[0]
            logo_color = np.array(Image.open(
                os.path.join(d, logo_path + logo_file)))

    for file_name in os.listdir(logo_path):
        if file_name.startswith(channel_name):
            print("🔎 Logo found: " + file_name)
            file_logo = file_name
            break

    if file_logo == "":
        print("❌ No logo found for " + channel_name)
        continue

    logo_color = np.array(Image.open(os.path.join(d, logo_path + file_logo)))
    print("🎨 Logo color generated for " + channel_name)

    # subsample by factor of 3. Very lossy but for a wordcloud we don't really care.
    logo_color = logo_color[::3, ::3]

    # create mask  white is "masked out"
    logo_mask = logo_color.copy()
    logo_mask[logo_mask.sum(axis=2) == 0] = 255
    print("🖍️  Logo mask generated for " + channel_name)

    # some finesse: we enforce boundaries between colors so they get less washed out.
    # For that we do some edge detection in the image
    edges = np.mean(
        [gaussian_gradient_magnitude(
            logo_color[:, :, i] / 255.0, 2) for i in range(3)],
        axis=0,
    )
    print("✍️  Logo edges generated for " + channel_name)

    logo_mask[edges > 0.08] = 255

    # create wordcloud. A bit sluggish, you can subsample more strongly for quicker rendering
    # relative_scaling=0 means the frequencies in the data are reflected less
    # acurately but it makes a better picture
    wc = WordCloud(
        max_words=10000,
        mask=logo_mask,
        max_font_size=20,
        random_state=42,
        relative_scaling=0,
    )
    print("🔠 Wordcloud generated for " + channel_name)

    # generate word cloud
    wc.generate(text)
    plt.imshow(wc)

    # create coloring from image
    image_colors = ImageColorGenerator(logo_color)
    wc.recolor(color_func=image_colors)
    plt.figure(figsize=(10, 10))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    wc.to_file("./../image/" + channel_name +
               "_" + dateFormated + ".png")
    print("💾 Image saved for " + channel_name)

    if channel_name == "":
        continue

    # load chat transcript text file
    try:
        text = open(
            os.path.join(d, "./../user/" + channel_name + ".txt"), encoding="utf-8"
        ).read()
    except:
        print("❌ No user transcript found for " + channel_name)
        continue

    wc.generate(text)
    plt.imshow(wc)

    # create coloring from image
    image_colors = ImageColorGenerator(logo_color)
    wc.recolor(color_func=image_colors)
    plt.figure(figsize=(10, 10))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    wc.to_file("./../image/" + channel_name + '_user' +
               "_" + dateFormated + ".png")
    print("💾 Image USER saved for " + channel_name)

    if channel_name == "":
        continue

    if "user" in sentences.get(channel_name, {}):
        sentenceUser = sentences[channel_name]["user"]
    else:
        sentenceUser = "Si tu fais partie des spectateurs les plus fidèles, tu figures obligatoirement sur ce beau dessin."

    mediaRecapWord = apiOld.media_upload(channel_name+".png", file=open("./../image/" + channel_name +
                                                                        "_" + dateFormated + ".png", "rb"))

    # Envoi d'un tweet
    tweetSend = api.create_tweet(
        text="C'est la fin de #gpexplorer2, félicitations à tous les participants ! Voici les mots les plus fréquemment utilisés dans le tchat pendant l'événement.\nEncore merci à @xSqueeZie pour cette masterclass !!!",
        media_ids=[mediaRecapWord.media_id]
    )

    tweet_id = tweetSend.data.get('id')

    print("🐧 Tweet CHANNEL sent for " + channel_name)

    try:
        # Envoi d'un media
        mediaRecapUser = apiOld.media_upload(channel_name+"_user.png",
                                             file=open("./../image/" + channel_name + '_user' +
                                                       "_" + dateFormated + ".png", "rb"))

        # Envoi d'un tweet
        tweetSend = api.create_tweet(
            text="Si tu apparais sur l'image, cela signifie que tu fais partie des meilleurs spectateurs du #gpexplorer2. 🏎️",
            in_reply_to_tweet_id=tweet_id,
            media_ids=[mediaRecapUser.media_id]
        )

        print("🐧 Tweet USER sent for " + channel_name)
    except:
        print("Bug send Twitter")

    # Deplacer le fichier dans un dossier archive
    shutil.move("./../tchat/" + channel_name + ".txt",
                "./../archive-tchat/" + channel_name + "_" + dateFormated + ".txt")

    # Deplacer le fichier dans un dossier archive
    shutil.move("./../user/" + channel_name + ".txt",
                "./../archive-user/" + channel_name + "_" + dateFormated + ".txt")


print("🚀 All images generated")
nextDayList()


# if os.path.exists("./../tchat/" + file):
#     os.remove("./../tchat/" + file)
#     print("✅ File " + file + " deleted")
# else:
#     print(f"{'./../tchat/'+file} n'existe pas")

# plt.figure(figsize=(10, 10))
# plt.title("Original Image")
# plt.imshow(logo_color)

# plt.figure(figsize=(10, 10))
# plt.title("Edge map")
# plt.imshow(edges)
# plt.axis("off")
# plt.show()
