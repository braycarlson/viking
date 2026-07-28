## Commands

Every public command is available as a prefix command using `*` and as a
slash command. Slash commands only appear after an owner runs `*sync`.
Commands that are marked as hidden are prefix-only.

Viking also registers an **About** user context menu, which shows the same
overview as `*about` from a member's right-click menu.

### **Activity**

***channels**
* Viking displays the most active voice channels in the server.

***devices \<member>**
* Viking displays how much time a member spends online on desktop, web and mobile.

***duo \<member>**
* Viking displays the members a member shares the most voice time with.

***games \<member>**
* Viking displays the most played games in the server, or for a single member.

***lastseen \<member>**
* Viking displays when a member was last online, and their most recent game and voice channel.

***music \<member>**
* Viking displays the most listened-to artists in the server, or for a single member.

***nowplaying**
* Viking displays every member currently playing a game.

***online**
* Viking displays the members with the most time spent online.

***social \<member>**
* Viking renders a friendship graph from shared voice, game and listening activity.

***songs \<member>**
* Viking displays the most listened-to songs in the server, or for a single member.

***streamers**
* Viking displays the members who spend the most time streaming in voice.

***voice \<member>**
* Viking displays the most active members in voice, or the favourite channels of a single member.

***wrapped \<member>**
* Viking displays a personal recap of a member's tracked activity.

### **Administration**

All of the following are hidden. Every command except `*hidden` is
restricted to the owner; `*hidden` requires the **Manage Server** permission.

***hidden**
* Viking displays the hidden commands that are available to administrators and moderators.

***kill**
* Viking closes all database connections, and logs out of Discord.

***load \<extension>**
* Viking loads an extension.

***reload \<extension>**
* Viking reloads an extension.

***respawn**
* Viking restarts itself without rebooting the Raspberry Pi.

***restart**
* Viking restarts my Raspberry Pi, and subsequently itself.

***sync \<~>**
* Viking synchronizes the application command tree, globally or to the current guild.

***unload \<extension>**
* Viking unloads an extension.

***wake**
* Viking wakes a PC with a magic packet.

***wipe**
* Viking wipes all log files.

### **Audio**

***add \<filename>**
* Viking adds an attached sound to the soundbank. This command is prefix-only.

***addtag \<sound> \<tag>**
* Viking adds a tag to a sound.

***browse**
* Viking displays an interactive soundbank.

***connect \<channel>**
* Viking connects to a voice channel.

***delete \<sound>**
* Viking deletes a sound that was uploaded by the author.

***mysounds**
* Viking displays every sound that was uploaded by the author.

***pause**
* Viking pauses the current sound.

***play \<sound>**
* Viking plays a sound from the soundbank that matches the member's query.

***removetag \<sound> \<tag>**
* Viking removes a tag from a sound.

***rename \<before> \<after>**
* Viking renames a sound that was uploaded by the author.

***resume**
* Viking resumes the current sound.

***skip**
* Viking skips the current sound, and plays the next sound in the queue.

***soundsfrom \<member>**
* Viking displays every sound that was uploaded by a member.

***stop**
* Viking stops the current sound, and removes any items from the queue.

***tags \<sound>**
* Viking displays the tags for a sound.

***themes**
* Viking displays the sound themes to browse.

**/upload**
* Viking opens a modal with a file picker to add a sound. This command is slash-only.

### **Basic**

***coinflip**
* Viking flips a coin.

***count \<message>**
* Viking counts the words in a message, excluding punctuation.

***dice**
* Viking rolls a dice.

***divide**
* Viking divides the members of a voice channel into groups.

***eightball \<question>**
* Viking answers a closed question.

***hello**
* Viking responds with a random greeting.

***mock \<message>**
* Viking "mocks" a message.

***quotes**
* Viking displays a random quotation.

***repeat \<amount> \<message>**
* Viking repeats the message a specified amount of times.

***reverse \<message>**
* Viking reverses the words in a message.

***tts \<message>**
* Viking uses text-to-speech to repeat the message.

***uptime**
* Viking displays its uptime.

### **Guild**

***invite**
* Viking generates an invite link to the server.

***members**
* Viking displays the total amount of members in the Discord server.

***nicknames**
* Viking displays the total amount of members with nicknames in the Discord server.

***owner**
* Viking mentions the owner of the server.

***ping**
* Viking displays the latency to the Discord server.

### **League of Legends**

***build \<champion>**
* Viking displays a recommended item build for a champion.

***champion \<champion>**
* Viking displays a champion's statistics.

***game \<riot_id>**
* Viking displays an overview of everyone in an active game including: name, level, champion, rank and win/loss ratio. Takes a Riot ID such as `Name#NA1`.

***rune \<champion>**
* Coming soon. The OPGG data source behind this command was removed and is being replaced.

***skill \<champion>**
* Coming soon. The OPGG data source behind this command was removed and is being replaced.

***spell \<spell>**
* Viking displays a summoner spell's statistics.

***summoner \<riot_id>**
* Viking provides you with information regarding a League of Legends account including: name, level, rank, points, win/loss ratio, and the top five champions with the highest mastery points. Takes a Riot ID such as `Name#NA1`.

### **Members**

***about \<member>**
* Viking displays an overview of a member.

***created \<member>**
* Viking displays the date of when a member created their Discord account.

***id \<member>**
* Viking displays the name of a member from an ID.

***joined \<member>**
* Viking displays the date of when a member joined the guild.

### **Migration**

All of the following are hidden, and restricted to the owner.

***create**
* Viking creates every table in the database(s).

***drop**
* Viking drops every table in the database(s).

***run**
* Viking inserts the members, roles and sounds into the database(s).

***update**
* Viking reconciles the public command registry with the commands it has loaded.

***update_public**
* Viking reconciles the public command registry and reports the result, without deleting the invoking message.

### **Moderation**

All of the following are hidden, except `*timeout` and `*untimeout`, which are
public and are also available as slash commands.

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

***kick \<member>**
* Viking kicks a member by name, nickname or ID.

***mute \<member>**
* Viking mutes a member by name, nickname or ID.

***purge**
* Viking purges the most recent messages from a text channel, up to 1000.

***restrict \<member>**
* Viking chat-restricts a member by name, nickname or ID, by assigning a `Restricted` role. The role is created on first use. Requires **Manage Roles**.

***softdeafen \<seconds> \<member>**
* Viking soft-deafens a member by name, nickname or ID, then undeafens them when the duration elapses or early if Viking shuts down.

***softmute \<seconds> \<member>**
* Viking soft-mutes a member by name, nickname or ID, then unmutes them when the duration elapses or early if Viking shuts down.

***softrestrict \<seconds> \<member>**
* Viking soft-restricts a member by name, nickname or ID, then unrestricts them when the duration elapses or early if Viking shuts down. Requires **Manage Roles**.

***timeout \<minutes> \<member>**
* Viking times a member out using Discord's native timeout, so it survives a restart. Requires **Moderate Members**.

***unban \<member>**
* Viking unbans a member by name, nickname or ID.

***undeafen \<member>**
* Viking undeafens a member by name, nickname or ID.

***unmute \<member>**
* Viking unmutes a member by name, nickname or ID.

***unrestrict \<member>**
* Viking unrestricts a member by name, nickname or ID. Requires **Manage Roles**.

***untimeout \<member>**
* Viking removes a timeout from a member by name, nickname or ID. Requires **Moderate Members**.

### **National Hockey League**

***leaders**
* Viking displays the NHL skater points leaders.

***player \<name>**
* Viking displays an NHL player's profile and current season statistics.

***roster \<team>**
* Viking displays a team's active roster.

***schedule \<team>**
* Viking displays a team's schedule for the current week.

***scores**
* Viking displays the scores for today's NHL games.

***standings**
* Viking displays the current NHL standings by division.

### **Roles**

***addrole \<role> \<member>**
* Viking adds a role to a member by name, nickname or ID. This command is hidden.

***createrole \<role>**
* Viking creates a role with no permissions. This command is hidden.

***deleterole \<role>**
* Viking deletes a role. This command is hidden.

***removerole \<role> \<member>**
* Viking removes a role from a member by name, nickname or ID. This command is hidden.

***role \<role>**
* Viking displays an overview of a role.

***rolepanel**
* Viking posts a self-service role panel that members can use to toggle their own roles. This command is hidden.

### **Weather**

***forecast \<location>**
* Viking will return the forecast of a specified location.
