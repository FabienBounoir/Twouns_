require('dotenv').config(); // pour lire les variables d'environnement
const tmi = require('tmi.js'); // pour utiliser l'API Twitch
const fs = require('fs'); // pour enregistrer le texte dans un fichier
// const badWords = require('bad-words');
// const filter = new badWords();
// const cleanMessage = filter.clean(message);
const filteredBot = require('./filteredBot.json');

// Connexion à l'API Twitch
const client = new tmi.Client({
    options: { debug: true },
    connection: {
        reconnect: true,
        secure: true
    },
    channels: process.env.TWITCH_CHANNELS.split(',') // récupération des chaînes à écouter depuis le fichier .env
});

// Enregistrement des messages de tchat dans un fichier
client.on('message', (channel, tags, message, self) => {
    if (self) return; // ignore les messages envoyés par le bot lui-même

    let date = new Date(); // récupération de la date

    if (filteredBot.includes(tags.username) || (tags.username == (channel.replace("#", "")))) return; // ignore les messages envoyés par les bots filtrés
    fs.appendFileSync(`./tchatTranscript/chat-${channel}-${date.getMonth() + 1}-${date.getFullYear()}.txt`, `${message}\n`); // enregistrement du message dans un fichier
});

// Connexion au client
client.connect();