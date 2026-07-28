## Viking

Viking is a Discord bot built on [discord.py](https://github.com/Rapptz/discord.py).

## Getting Started

You will need:
* [Python 3.14+](https://www.python.org/downloads/)
* [PostgreSQL 11+](https://www.postgresql.org/download/) with the `fuzzystrmatch` extension
* [uv](https://github.com/astral-sh/uv)
* [FFmpeg](https://ffmpeg.org/download.html) for audio playback

## Requirements

Install the requirements:
```
$ uv sync
```

## Configuration

Viking reads a `config.ini` file from the root of the project. It is not tracked
by git. Copy the example and fill it in:

```
$ cp config.example.ini config.ini
```

Every guild gets its own database. A guild is one line in `[guilds]`. The
`command` and `lol` databases are shared. Viking creates them at the same time.

The `[paramiko]` section is for the owner-only administration commands. The
`wake_command` setting is the shell command that `*wake` runs over SSH to send a
magic packet. An example is `bash /home/user/wol.sh`. If it is not set, `*wake`
says so instead of failing.

Viking creates `.logs`, `.sound/default`, `.sound/member` and
`images/lol/champion` on startup. A fresh clone needs no manual setup. Those
directories are not tracked by git.

## Running

```
$ uv run run.py
```

The `run.py` script validates `config.ini` before it connects. It reports the
missing file or sections instead of failing part-way through startup.

On a server, use `run.sh`. It wraps `run.py` in a respawn loop and waits for the
network first. It resolves its own directory, so it can live anywhere and start
from anywhere:

```
$ ./run.sh
```

The wrapper relaunches `run.py` on any exit. The `*respawn` command relies on
that. The `*kill` command writes a `.stop` file instead. The wrapper sees the
file and exits with it.

## Features

Viking is split into thirteen extensions. Each one is a self-contained package.
The bot finds and loads them at startup.

* **Activity**: records presence, voice, game and Spotify sessions. It reports
  leaderboards, a personal recap, and a rendered friendship graph.
* **Administration**: owner-only control over the process and its extensions.
* **Audio**: a tagged soundbank with an interactive, paginated browser.
* **Basic**: small utility and novelty commands.
* **Guild**: server-level counts and latency.
* **League of Legends** - champion, item, spell and summoner lookups against the
  Riot API.
* **Members**: stored member profiles, including previous names and nicknames.
* **Migration**: owner-only schema creation and command registry reconciliation.
* **Moderation**: bans, kicks, timeouts, and timed voice and chat restrictions.
* **National Hockey League** - scores, standings, rosters, schedules and leaders.
* **Roles**: role management and a self-service role panel.
* **Synchronization**: a nightly task that reconciles the stored members and
  roles against Discord.
* **Weather**: the current forecast for a location.

Every public command works as a prefix command with `*` and as a slash command.
The slash commands appear after an owner runs `*sync`. A hidden command is
prefix-only.

The reference for all 104 commands is in [COMMANDS.md](COMMANDS.md).

## License

The project is licensed under the MIT License. See the [LICENSE](LICENSE) file
for details.
