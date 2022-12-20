from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


lol = Path(__file__).parent.parent.joinpath('images/lol')


class SkillOrder:
    def __new__(self, data):
        skills, images = data
        q, w, e, r = images[0]

        path = lol.joinpath('spell')

        q = path.joinpath(q)
        q = Image.open(q)

        w = path.joinpath(w)
        w = Image.open(w)

        e = path.joinpath(e)
        e = Image.open(e)

        r = path.joinpath(r)
        r = Image.open(r)

        row = len(skills)
        column = 1
        offset = 16

        width = height = 64

        size = (
            (row - 1) * width + (row * offset),
            (column * height) + (column * offset)
        )

        color = (255, 0, 0, 0)
        grid = Image.new('RGBA', size=size, color=color)

        x = (offset * row) // (row + 1)
        y = (offset * column) // (column + 1)

        for skill in skills:
            match skill:
                case 'Q':
                    image = q.copy()
                    dimension = (6.5, 2.5)
                case 'W':
                    image = w.copy()
                    dimension = (6, 2.5)
                case 'E':
                    image = e.copy()
                    dimension = (8, 2.5)
                case 'R':
                    image = r.copy()
                    dimension = (7, 2.5)

            background = Image.new(
                'LA',
                size=(28, 28),
                color=0
            )

            background.putalpha(192)

            draw = ImageDraw.Draw(background)

            font = ImageFont.truetype(
                'C:/Windows/Fonts/Arial.ttf',
                18
            )

            draw.text(
                dimension,
                skill,
                font=font,
            )

            image.paste(
                background,
                (36, 40),
                mask=background
            )

            box = (x, y)
            grid.paste(image, box=box)

            x = x + (width + 10)

        return grid
