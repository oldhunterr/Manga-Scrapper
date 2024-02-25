from .database import db

class Source(db.Model):
    __tablename__ = 'Sources'

    source_id = db.Column('SourceID',db.Integer, primary_key=True)
    source_name = db.Column('SourceName',db.String(100), nullable=False)
    source_url = db.Column('SourceURL',db.String(255), nullable=False)

    @staticmethod
    def get_sources():
        return Source.query.all()
