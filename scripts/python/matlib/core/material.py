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

        self._name = name
        self._fav = fav
        self._renderer = renderer
        self.date = date
        self._builder = builder
        self._usd = usd

        self._cats = [""] if not cats else cats
        self._tags = [""] if not tags else tags
        self._mat_id = str(uuid.uuid1().time) if mat_id == "" else mat_id

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
            "id": self._mat_id,
            "name": self._name,
            "categories": self._cats,
            "tags": self._tags,
            "favorite": self._fav,
            "date": self._date,
            "renderer": self._renderer,
            "usd": self._usd,
            "builder": self._builder,
        }

        return material_dict

    @property
    def mat_id(self) -> str:
        return str(self._mat_id)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        self._name = new_name

    @property
    def date(self) -> str:
        return self._date

    @date.setter
    def date(self, date: str = "") -> None:
        self._date = date if date != "" else str(datetime.datetime.now())[:-7]

    @property
    def fav(self) -> bool:
        return self._fav

    @fav.setter
    def fav(self, fav: bool) -> None:
        self._fav = fav

    @property
    def renderer(self) -> str:
        return self._renderer

    @property
    def builder(self) -> int:
        return self._builder

    @property
    def tags(self) -> list[str]:
        return self._tags

    @tags.setter
    def tags(self, tags: str) -> None:
        tag = tags.split(",")
        for c in tag:
            c = c.replace(" ", "")
        self._tags = tag

    @property
    def usd(self) -> int:
        return self._usd

    @property
    def categories(self) -> list[str]:
        return self._cats

    @categories.setter
    def categories(self, cats: str) -> None:
        cat = cats.split(",")
        for c in cat:
            c = c.replace(" ", "")
        self._cats = cat

    def remove_category(self, cat: str) -> None:
        if cat in self._cats:
            self._cats.remove(cat)

    def rename_category(self, old: str, new: str) -> None:
        for index, cat in enumerate(self._cats):
            if old == cat:
                self._cats[index] = new
