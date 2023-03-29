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
    with open("channel-order.json", "r") as f:
        liste_arrays = json.load(f)

    # Récupérer la première array et la supprimer de la liste
    premiere_array = liste_arrays.pop(0)

    # Ajouter la première array à la fin de la liste
    liste_arrays.append(premiere_array)

    # Ouvrir le fichier en mode écriture et écrire la liste mise à jour
    with open("channel-order.json", "w") as f:
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
api = tweepy.API(auth)
print("🔓 Authentification Twitter")

# Date du jour
date = datetime.now()
dateFormated = date.strftime("%d-%m-%Y_%H:%M:%S")

# get the channel order
with open('channel-order.json', 'r') as f:
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

with open('customTextTweet.json') as f:
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

    # Envoi d'un tweet
    tweetSend = api.update_status_with_media(
        "Voici le récapitulatif des 30 derniers jours sur le chat de @"
        + twitter_name +
        " !\n#Twouns_ #Stats #" +
        channel_name
        + " #Twitch",
        channel_name+".png",
        file=open("./../image/" + channel_name +
                  "_" + dateFormated + ".png", "rb"),
    )

    print("🐧 Tweet CHANNEL sent for " + channel_name)

    # Deplacer le fichier dans un dossier archive
    shutil.move("./../tchat/" + channel_name + ".txt",
                "./../archive-tchat/" + channel_name + "_" + dateFormated + ".txt")

    # load chat transcript text file
    try:
        text = open(
            os.path.join(d, "./../user/" + channel_name + ".txt"), encoding="utf-8"
        ).read()
    except:
        print("❌ No user transcript found for " + channel_name)
        continue

    tweet_id = tweetSend.id

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

    # Envoi d'un tweet
    tweetSend = api.update_status_with_media(
        sentenceUser +
        " #" +
        channel_name,
        channel_name+"_user.png",
        file=open("./../image/" + channel_name + '_user' +
                  "_" + dateFormated + ".png", "rb"),
        in_reply_to_status_id=tweet_id
    )

    print("🐧 Tweet USER sent for " + channel_name)

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
