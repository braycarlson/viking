from database.engine import command


class Public(command.Model):
    __tablename__ = 'public'

    id = command.Column(command.Integer(), primary_key=True)
    name = command.Column(command.TEXT(), nullable=False)
    aliases = command.Column(command.ARRAY(command.TEXT()), nullable=True)

    _idx_public_command_name = command.Index('index_public_name', 'name', unique=True)


class Hidden(command.Model):
    __tablename__ = 'hidden'

    id = command.Column(command.Integer(), primary_key=True)
    name = command.Column(command.TEXT(), nullable=False)
    aliases = command.Column(command.ARRAY(command.TEXT()), nullable=True)

    _idx_hidden_command_name = command.Index('index_hidden_name', 'name', unique=True)
