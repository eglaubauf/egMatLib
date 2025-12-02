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

        self.name = name
        self.fav = fav
        self.renderer = renderer
        self.date = date
        self.builder = builder
        self.usd = usd

        self.cats = [""] if not cats else cats
        self.tags = [""] if not tags else tags
        self.mat_id = str(uuid.uuid1().time) if mat_id == "" else mat_id
        self.date = self.set_date() if date == "" else date

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
            "id": self.mat_id,
            "name": self.name,
            "categories": self.cats,
            "tags": self.tags,
            "favorite": self.fav,
            "date": self.date,
            "renderer": self.renderer,
            "usd": self.usd,
            "builder": self.builder,
        }

        return material_dict

    def get_id(self) -> str:
        return self.mat_id

    def get_name(self) -> str:
        return self.name

    def set_name(self, new_name: str) -> None:
        self.name = new_name

    def set_date(self) -> str:
        date = str(datetime.datetime.now())
        return date[:-7]

    def get_date(self) -> str:
        return self.date

    def get_fav(self) -> bool:
        return self.fav

    def set_fav(self, fav: bool) -> None:
        self.fav = fav

    def get_tags(self) -> list[str]:
        return self.tags

    def get_usd(self) -> int:
        return self.usd

    def get_categories(self) -> list[str]:
        return self.cats

    def set_categories(self, cats: str) -> None:
        cat = cats.split(",")
        for c in cat:
            c = c.replace(" ", "")
        self.cats = cat

    def remove_category(self, cat: str) -> None:
        if cat in self.cats:
            self.cats.remove(cat)

    def rename_category(self, old: str, new: str) -> None:
        for cat in self.cats:
            if old in cat:
                cat = new

    def set_tags(self, tags: str) -> None:
        tag = tags.split(",")
        for c in tag:
            c = c.replace(" ", "")
        self.tags = tag

    def get_renderer(self) -> str:
        return self.renderer

    def get_builder(self) -> int:
        return self.builder
