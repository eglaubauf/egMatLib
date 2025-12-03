from __future__ import annotations
import uuid
import datetime


class Material:
    def __init__(
        self,
        name: str = "",
        cats: list[str] | None = None,
        tags: list[str] | None = None,
        fav: bool = False,
        renderer: str = "MatX",
        date: str = "",
        builder: int = 0,
        usd: int = 1,
        mat_id: str = "",
    ):

        self.__name = name
        self.__fav = fav
        self.__renderer = renderer
        self.date = date
        self.__builder = builder
        self.__usd = usd

        self.__cats = [""] if not cats else cats
        self.__tags = [""] if not tags else tags
        self.__mat_id = str(uuid.uuid1().time) if mat_id == "" else mat_id

    @classmethod
    def from_dict(cls, material_dict: dict) -> Material:

        name = material_dict["name"]
        cats = material_dict["categories"]
        tags = material_dict["tags"]
        fav = material_dict["favorite"]
        mat_id = material_dict["id"]
        date = material_dict["date"]
        renderer = material_dict["renderer"]
        usd = material_dict["usd"]
        builder = material_dict["builder"]

        return cls(name, cats, tags, fav, renderer, date, builder, usd, mat_id)

    def get_as_dict(self) -> dict:
        material_dict = {
            "id": self.__mat_id,
            "name": self.__name,
            "categories": self.__cats,
            "tags": self.__tags,
            "favorite": self.__fav,
            "date": self.__date,
            "renderer": self.__renderer,
            "usd": self.__usd,
            "builder": self.__builder,
        }

        return material_dict

    @property
    def mat_id(self) -> str:
        return str(self.__mat_id)

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, new_name: str) -> None:
        self.__name = new_name

    @property
    def date(self) -> str:
        return self.__date

    @date.setter
    def date(self, date: str = "") -> None:
        self.__date = date if date != "" else str(datetime.datetime.now())[:-7]

    @property
    def fav(self) -> bool:
        return self.__fav

    @fav.setter
    def fav(self, fav: bool) -> None:
        self.__fav = fav

    @property
    def renderer(self) -> str:
        return self.__renderer

    @property
    def builder(self) -> int:
        return self.__builder

    @property
    def tags(self) -> list[str]:
        return self.__tags

    @tags.setter
    def tags(self, tags: str) -> None:
        tag = tags.split(",")
        for c in tag:
            c = c.replace(" ", "")
        self.__tags = tag

    @property
    def usd(self) -> int:
        return self.__usd

    @property
    def categories(self) -> list[str]:
        return self.__cats

    @categories.setter
    def categories(self, cats: str) -> None:
        cat = cats.split(",")
        for c in cat:
            c = c.replace(" ", "")
        self.__cats = cat

    def remove_category(self, cat: str) -> None:
        if cat in self.cats:
            self.cats.remove(cat)

    def rename_category(self, old: str, new: str) -> None:
        for cat in self.cats:
            if old in cat:
                cat = new
