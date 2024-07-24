import os
import re
import tweepy
import numpy as np
import matplotlib.pyplot as plt
import json
import shutil

import tkinter as tk
import requests

from PIL import Image
from datetime import datetime, timedelta
from scipy.ndimage import gaussian_gradient_magnitude
from wordcloud import WordCloud, ImageColorGenerator
from dotenv import load_dotenv

from collections import Counter
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from enum import Enum


class Folder(Enum):
    EMOTE = "emote"
    TCHAT = "tchat"
    USER = "user"


# def nextDayList():
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

def read_first_10_mb(file_path, less_one_mb=False):
    buffer_size = 1024 * 1024  # 1 Mo
    min_size = buffer_size  # 1 Mo
    max_size = 10 * buffer_size  # 10 Mo

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = ''
            while len(data.encode('utf-8')) < max_size:
                chunk = file.read(buffer_size)
                if not chunk:
                    break
                data += chunk
                if len(data.encode('utf-8')) >= min_size:
                    return data  # Retourne les données dès qu'elles dépassent 1 Mo

            if less_one_mb:
                return data

            return '__LESS_THAN_1MB__'  # Retourne une valeur spécifique pour indiquer moins de 1 Mo
    except FileNotFoundError:
        print("❌ No user transcript found for " + channel_name)
        return None  # Retourne None si le fichier est introuvable



def get_font_size(text, max_font_size):
    font = ImageFont.truetype("../assets/Oswald.ttf", size=max_font_size)

    while font.getlength(text) > 380:
        max_font_size -= 1
        font = ImageFont.truetype("../assets/Oswald.ttf", size=max_font_size)

    return font


def set_token_twitch():
    client_id = os.getenv("TWITCH_CLIENT_ID")
    client_secret = os.getenv("TWITCH_CLIENT_SECRET")

    # URL de l'endpoint Twitch pour obtenir un jeton d'accès
    token_url = f"https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials"

    try:
        # Effectuer la demande POST pour obtenir le jeton d'accès
        response = requests.post(token_url)
        response.raise_for_status()

        # Obtenir les informations du jeton d'accès à partir de la réponse JSON
        info_token = response.json()

        # Définir le jeton Twitch dans l'objet client
        return info_token["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"Erreur : {e}")


def get_twitch_profile_picture(username):
    client_id = os.getenv("TWITCH_CLIENT_ID")

    # Define the Twitch API URL
    url = f'https://api.twitch.tv/helix/users?login={username}'

    # Set up the headers with your Client ID and Client Secret
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {token_twitch}'
    }

    try:
        # Make a GET request to the Twitch API
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        # Get the user's profile picture URL from the response
        profile_picture_url = data['data'][0]['profile_image_url']

        response = requests.get(profile_picture_url)

        # Vérifiez si le téléchargement s'est bien passé (statut 200)
        if response.status_code == 200:
            # Obtenez le contenu de l'image
            image_avatar = Image.open(BytesIO(response.content))

            nouvelle_taille = (
                145, int(image_avatar.height * (145 / image_avatar.width)))
            image_avatar = image_avatar.resize(nouvelle_taille)

            return image_avatar
        else:
            raise Exception("Erreur lors du téléchargement de l'image.")

    except Exception as e:
        image_avatar = Image.open("../assets/defaultAvatar.png")

        nouvelle_taille = (
            145, int(image_avatar.height * (145 / image_avatar.width)))
        image_avatar = image_avatar.resize(nouvelle_taille)

        return image_avatar


def getText(folder, channel):
    print("📝 Récupération "+folder+" pour la chaine " + channel)
    texte = ""

    # Récupérer les textes
    with open("../"+folder+"/"+channel+".txt", "r") as f:
        texte += f.read()

    return texte


def getCountAndSize(text, top, split):
    arrayElement = text.split(split)
    arrayElement.pop()

    arrayCounter = Counter(arrayElement)

    sorted_emotes = sorted(arrayCounter.items(),
                           key=lambda x: x[1], reverse=True)

    size = len(sorted_emotes)
    sorted_emotes = sorted_emotes[:top]

    return sorted_emotes, size

def getCountAfterSplit(text, split):
    arrayElement = text.split(split)
    arrayElement.pop()

    size = len(arrayElement)

    return size


# load env variables
print("🔄 Load env variables")
load_dotenv()

# Twitter API credentials
consumer_key = os.getenv("API_KEY")
consumer_secret = os.getenv("API_SECRET_KEY")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

# Twitch Token
token_twitch = set_token_twitch()

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
with open('channel-order.json', 'r') as f:
    data = json.load(f)


# extraire la liste du jour
channels_of_the_day = data[0]

# check if array is empty
if not channels_of_the_day:
    print("❌ No channel found for this date")
    # nextDayList()
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
        text = read_first_10_mb(os.path.join(d, "./../tchat/" + channel_name + ".txt"))
        
        if text is None:
            print("❌ No tchat transcript found for " + channel_name)
            continue
        elif text == '__LESS_THAN_1MB__':
            print("Le fichier tchat de " + channel_name + " est inférieur à 1 Mo, ACTION SKIP...")
            continue
    except:
        print("❌ No tchat transcript found for " + channel_name)
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
        max_words=2000,
        mask=logo_mask,
        max_font_size=40,
        random_state=42,
        relative_scaling=0,
        repeat=True,
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
        text = read_first_10_mb(os.path.join(d, "./../user/" + channel_name + ".txt"), True)

        if text is None:
            print("❌ No user transcript found for " + channel_name)
            continue
        
        open(
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

    # ---------------------------------

    emoteText = getText(Folder.EMOTE.value, channel_name)
    userText = getText(Folder.USER.value, channel_name)
    messageText = getText(Folder.TCHAT.value, channel_name)

    # Récupérer les emotes, users et messages
    emoteArray, emoteSize = getCountAndSize(emoteText, 5, ",")
    userArray, userSize = getCountAndSize(userText, 5, "\n")
    messageSize = getCountAfterSplit(messageText, "\n")

    largeur, hauteur = 2836, 1690
    image = Image.new('RGBA', (largeur, hauteur), color='#101010')

    # Chargez une image existante
    templateImage = Image.open('../assets/template.png')

    # Collez l'image sur l'image principale à une position spécifique
    image.paste(templateImage, (0, 0))
    draw = ImageDraw.Draw(image)

    couleur_texte = (255, 255, 255)

    for emote_id, count in emoteArray:
        print("🔎 Emote: " + emote_id)
        # Récupérer l'emote
        url_emote = "https://static-cdn.jtvnw.net/emoticons/v2/" + \
            emote_id.split("#")[1]+"/static/dark/3.0"
        response = requests.get(url_emote)

        # Vérifiez si le téléchargement s'est bien passé (statut 200)
        if response.status_code == 200:
            # Obtenez le contenu de l'image
            image_emote = Image.open(BytesIO(response.content))

            nouvelle_taille = (
                145, int(image_emote.height * (145 / image_emote.width)))
            image_emote = image_emote.resize(nouvelle_taille)

            # Collez l'image de l'emote sur l'image principale à une position spécifique
            position_x, position_y = 229, 404 + \
                (emoteArray.index((emote_id, count)) * 145 +
                 62 * emoteArray.index((emote_id, count)))

            try:
                image.paste(image_emote, (position_x, position_y), image_emote)
            except:
                image.paste(image_emote, (position_x, position_y))

            draw.text((1250, position_y+(145/2)),
                      "Envoyée " + str(count) + " fois", font=ImageFont.truetype("../assets/Oswald.ttf", size=70), fill=couleur_texte, anchor="rm")
        else:
            print("Erreur lors du téléchargement de l'image " + emote_id)

    for user, count in userArray:
        print("👤 User: " + user)

        # Récupérer l'emote
        image_avatar = get_twitch_profile_picture(user)

        position_x, position_y = 1589, 404 + \
            (userArray.index((user, count)) * 145 +
             62 * userArray.index((user, count)))

        image.paste(image_avatar, (position_x, position_y))

        font = get_font_size(user, 60)

        draw.text((position_x + 170, position_y+(145/2)), user,
                  font=font, fill=couleur_texte, anchor="lm")

        draw.text((2608, position_y+(145/2)),
                  str(count) + " Messages", font=ImageFont.truetype("../assets/Oswald.ttf", size=70), fill=couleur_texte, anchor="rm")

    # Ajoutez le texte à l'image
    draw.text((1418, 1530),
              f"{messageSize} messages ont été envoyés par {userSize} personnes",
              font=ImageFont.truetype("../assets/Oswald.ttf", size=80), fill=couleur_texte, anchor="mm")

    image.save("./../image/" + channel_name + '_top' +
               "_" + dateFormated + ".png")

    # ---------------------------------

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
        text="Voici le récapitulatif des 30 derniers jours sur le chat Twitch de @"
        + twitter_name +
        " !\n#" +
        channel_name,
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
            text=sentenceUser +
            " #" +
            channel_name,
            in_reply_to_tweet_id=tweet_id,
            media_ids=[mediaRecapUser.media_id]
        )

        print("🐧 Tweet USER send for " + channel_name)
    except:
        print("Bug send Tweet User")

    tweet_id = tweetSend.data.get('id')

    try:
        # Envoi d'un media
        mediaRecapUser = apiOld.media_upload(channel_name+"_top.png",
                                             file=open("./../image/" + channel_name + '_top' +
                                                       "_" + dateFormated + ".png", "rb"))

        # Envoi d'un tweet
        tweetSend = api.create_tweet(
            text=f"Hello @{twitter_name} 👋,\nVoici un petit récapitulatif qui pourrait t'intéresser sur les emotes🎉 et les utilisateurs👤 qui se sont le plus manifestés sur ton tchat #Twitch #"+channel_name,
            in_reply_to_tweet_id=tweet_id,
            media_ids=[mediaRecapUser.media_id]
        )

        print("🐧 Tweet TOP send for " + channel_name)
    except:
        print("Bug send TOP Tweet")

    # Deplacer le fichier dans un dossier archive
    # shutil.move("./../tchat/" + channel_name + ".txt",
    #             "./../archive-tchat/" + channel_name + "_" + dateFormated + ".txt")

    # # Deplacer le fichier dans un dossier archive
    # shutil.move("./../user/" + channel_name + ".txt",
    #             "./../archive-user/" + channel_name + "_" + dateFormated + ".txt")

    # # Deplacer le fichier dans un dossier archive
    # shutil.move("./../emote/" + channel_name + ".txt",
    #             "./../archive-emote/" + channel_name + "_" + dateFormated + ".txt")


print("🚀 All images generated")
# nextDayList()
