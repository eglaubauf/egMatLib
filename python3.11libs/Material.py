import hou
import uuid
import datetime

class Material:
    def __init__(
        self, name="", cats=None, tags=None, fav=False, renderer="MatX", date=None, builder=0, usd=1, id=None):


        self.name = name
        self.cats = cats
        self.tags = tags
        self.fav = fav
        self.renderer = renderer
        self.date = date
        self.builder = builder
        self.usd = usd

        if not id:
            self.id = uuid.uuid1().time
        else:
            self.id = id

        if not date:
            self.set_date()
        else:
            self.date = date

    @classmethod
    def from_dict(cls, dict):

        name = dict["name"]
        cats = dict["categories"]
        tags = dict["tags"]
        fav = dict["favorite"]
        id = dict["id"]
        date = dict["date"]
        renderer = dict["renderer"]
        usd = dict["usd"]
        builder = dict["builder"]

        return cls(name, cats, tags, fav, renderer, date, builder, usd, id)


    def get_as_dict(self):
        dict = {
            "id": self.id,
            "name": self.name,
            "categories": self.cats,
            "tags": self.tags,
            "favorite": self.fav,
            "date": self.date,
            "renderer": self.renderer,
            "usd": self.usd,
            "builder": self.builder
        }

        return dict

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def set_name(self, new_name):
        self.name = new_name

    def set_date(self):
        date = str(datetime.datetime.now())
        self.date = date[:-7]

    def get_date(self):
        return self.date

    def get_fav(self):
        return self.fav

    def set_fav(self, fav):
        self.fav = fav

    def get_tags(self):
        return self.tags

    def get_usd(self):
        return self.usd

    def get_categories(self):
        return self.cats

    def set_categories(self, cats):
        cat = cats.split(",")
        for c in cat:
            c = c.replace(" ", "")
        self.cats = cat

    def remove_category(self, cat):
        if cat in self.cats:
            self.cats.remove(cat)

    def rename_category(self, old, new):
        for cat in self.cats:
            if old in cat:
                cat = new

    def set_tags(self, tags):
        tag = tags.split(",")
        for c in tag:
            c = c.replace(" ", "")
        self.tags = tag

    def get_renderer(self):
        return self.renderer

    def get_builder(self):
        return self.builder
