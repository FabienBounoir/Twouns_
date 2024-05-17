const tmi = require('tmi.js'); // pour utiliser l'API Twitch
const fs = require('fs'); // pour enregistrer le texte dans un fichier
const filteredBot = require('./filteredBot.json');

console.log("[LOG] Twouns started")

//get file in directory
const channels = fs.readdirSync('./logoChannel').filter(file => file.endsWith('.png')).map(file => file.split("-")[0])

console.log("[LOG]    listen: ", channels)

// Connexion à l'API Twitch
const client = new tmi.Client({
    options: { debug: false, },
    connection: {
        reconnect: true,
        secure: true
    },
    channels // récupération des chaînes à écouter
});

// Enregistrement des messages de tchat dans un fichier
client.on('message', (channel, tags, message, self) => {
    if (self) return; // ignore les messages envoyés par le bot lui-même
    channel = channel.replace("#", "")

    if (filteredBot.includes(tags.username) || (tags.username == channel)) return; // ignore les messages envoyés par les bots filtrés

    if (tags.emotes) {
        let emotesValues = Object.entries(tags.emotes)

        let formatedEmotes = ""

        for (let [id, emotes] of emotesValues) {

            for (let emote of emotes) {
                let [start, end] = emote.split("-")


                let emoteName = message.slice(parseInt(start), parseInt(end) + 1)

                formatedEmotes += `${emoteName}#${id},`

                message = (message.replace(emoteName, " ".repeat(parseInt(end) - parseInt(start) + 1)))
            }
        }

        fs.appendFileSync(`./emote/${channel}.txt`, formatedEmotes)

        if (message.replace(/\s/g, '').length === 0) return
    }

    if (message.replace(/\s/g, '').length > 0) {
        message = message.replace(/\s\s+/g, ' ')

        fs.appendFileSync(`./tchat/${channel}.txt`, `${message}\n`); // enregistrement du message dans un fichier
    }

    fs.appendFileSync(`./user/${channel}.txt`, `${tags.username}\n`); // enregistrement du nom d'utilisateur dans un fichier
});

client.on('join', (channel, username, self) => {
    if (self) return; // ignore les messages envoyés par le bot lui-même

    channel = channel.replace("#", "")

    if (filteredBot.includes(username) || (username == channel)) return; // ignore les messages envoyés par les bots filtrés
    fs.appendFileSync(`./user/${channel}.txt`, `${username}\n`); // enregistrement du nom d'utilisateur dans un fichier
});

// Connexion au client
client.connect();