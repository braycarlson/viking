## Viking

Viking is a bot that uses [discord.py](https://github.com/Rapptz/discord.py).

## Getting Started

You will need:
* [Python 3.7](https://www.python.org/downloads/)
* [PostgreSQL 11](https://www.postgresql.org/download/)
* [Redis 5](https://redis.io/download)

## Requirements

You can install all of the requirements by running:
```
$ pip install -r requirements.txt
```

## Commands

### **Administration**

***kill**
* Viking closes all database connections, and log out of Discord.

***restart**
* Viking restarts my Raspberry Pi, and subsequently itself.

***wipe**
* Viking wipes all log files.

### **Basic**

***coinflip**
* Viking flips a coin.

***count \<message>**
* Viking counts the words in a message, excluding punctuation.

***dice**
* Viking rolls a dice.

***eightball \<question>**
* Viking answers a closed question.

***hello**
* Viking responds with a random greeting.

***quotes**
* Viking displays a random quotation.

***repeat \<amount> \<message>**
* Viking repeats the message a specified amount of times.

***reverse \<message>**
* Viking reverses the words in a message.

***tts \<message>**
* Viking uses text-to-speech to repeat the message.

***uptime**
* Viking displays it's uptime.

### **Database**

***drop**
* Viking drops all tables in the database.

***run**
* Viking executes the necessary queries to create the database.

***truncate \<table>**
* Viking truncates a table in the database.

### **Discord**

***administrators**
* Viking lists all of the administrators in the guild.

***help**
* Viking lists all available commands in the text channel.

***invite**
* Viking generates an invite link to the server.

***members**
* Viking displays the total amount of members in Discord server.

***moderators**
* Viking lists all of the moderators in the guild.

***nicknames**
* Viking displays the total amount of members with nicknames in Discord server.

***owner**
* Viking mentions the owner of the server.

***ping**
* Viking displays the latency to the Discord server.

### **Fortnite**

***fortnite \<platform> \<username>**
* Viking displays a member's Fortnite statistics, including
solo, duo, squad and lifetime data.

### **League of Legends**

***build \<champion>**
* Viking links you to the champion's most frequent and highest winning build path

***counters \<champion>**
* Viking links you to the champion's counters.

***champion \<champion>**
* Viking displays a champion's statistics.

***duo \<champion>**
* Viking links you to the champion's most successful duo.

***game \<username>**
* Viking displays an overview of everyone in an active game including: name, level, champion, rank and win/loss ratio.

***matchups \<champion>**
* Viking links you to the champion's most successful matchups in descending order.

***path \<champion>**
* Viking links you to the champion's most successful build path in descending order.

***probuild \<username>**
* Viking links you to a professional player's game, and show you how they played the champion.

***runes \<champion>**
* Viking links you to a champion's most successful rune page in descending order.

***spell \<spell>**
* Viking displays a summoner spell's statistics.

***summoner \<username>**
* Viking provides you with information regarding a League of Legends account including: name, level, rank, points, win/loss ratio, and the top five champions with the highest mastery points.

### **Members**
***about \<member>**
* Viking displays an overview of a member.

***created \<member>**
* Viking displays the date of when a member created their Discord account.

***id \<member>**
* Viking displays the name and discriminator of a member from an ID.

***joined \<member>**
* Viking displays the date of when a member joined the guild.

### **Moderation**

***afk \<member>**
* Viking moves a member by name, nickname or ID to a designated voice channel.

***ban \<member>**
* Viking bans a member by name, nickname or ID.

***clear \<amount>**
* Viking clears a specified amount of messages from a text channel.

***deafen \<member>**
* Viking deafens a member by name, nickname or ID.

***disconnect \<member>**
* Viking disconnects a member from a voice channel by name, nickname or ID.

***hidden**
* Viking displays hidden commands that are available for administrators/moderators to use.

***kick \<member>**
* Viking kicks a member by name, nickname or ID.

***load \<extension>**
* Viking loads an extension.

***mute \<member>**
* Viking mutes a member by name, nickname or ID.

***purge**
* Viking purges all messages from a text channel.

***reload \<extension>**
* Viking reloads an extension.

***restrict \<member>**
* Viking chat-restricts a member by name, nickname or ID.

***softdeafen \<seconds> \<member>**
* Viking soft-deafens a member by name, nickname or ID.

***softmute \<seconds> \<member>**
* Viking soft-mutes a member by name, nickname or ID.

***softrestricts \<seconds> \<member>**
* Viking soft-restricts a member by name, nickname or ID.

***unban \<member>**
* Viking unbans a member by name, nickname or ID.

***undeafen \<member>**
* Viking undeafens a member by name, nickname or ID.

***unload \<extension>**
* Viking unloads an extension.

***unmutes \<member>**
* Viking unmutes a member by name, nickname or ID.

***unrestrict \<member>**
* Viking unrestricts a member by name, nickname or ID.

### **Roles**

***addrole \<role> \<member>**
* Viking adds a role to a member by name, nickname or ID.

***createrole \<role>**
* Viking creates a role with no permissions.

***deleterole \<role>**
* Viking deletes a role.

***removerole \<role> \<member>**
* Viking removes a role from a member by name, nickname or ID.

***role \<role>**
* Viking displays an overview of the role.

### **Weather**

***forecast \<location>**
* Viking will return the forecast of a specified location.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
