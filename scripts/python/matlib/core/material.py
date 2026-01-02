"""
Holds Material information
"""

from __future__ import annotations
import uuid
import datetime


class Material:
    """
    Holds Material information
    """

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
        """
        Turns a dict, typically retrieved from the database into a Material Instance

        :param cls: Description
        :param material_dict: Description
        :type material_dict: dict
        :return: Description
        :rtype: Material
        """
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
        """
        Return the current Instance as a Dictionary
        Typically used before saving into the DB

        :param self: Description
        :return: Description
        :rtype: dict[Any, Any]
        """
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
        """
        Docstring for mat_id

        :param self: Description
        :return: Description
        :rtype: str
        """
        return str(self._mat_id)

    @property
    def name(self) -> str:
        """
        Docstring for name

        :param self: Description
        :return: Description
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        """
        Docstring for name

        :param self: Description
        :param new_name: Description
        :type new_name: str
        """
        self._name = new_name

    @property
    def date(self) -> str:
        """
        Docstring for date

        :param self: Description
        :return: Description
        :rtype: str
        """
        return self._date

    @date.setter
    def date(self, date: str = "") -> None:
        """
        Docstring for date

        :param self: Description
        :param date: Description
        :type date: str
        """
        self._date = date if date != "" else str(datetime.datetime.now())[:-7]

    def set_current_date(self) -> None:
        """
        Docstring for set_current_date

        :param self: Description
        """
        self.date = ""

    @property
    def fav(self) -> bool:
        """
        Docstring for fav

        :param self: Description
        :return: Description
        :rtype: bool
        """
        return self._fav

    @fav.setter
    def fav(self, fav: bool) -> None:
        """
        Docstring for fav

        :param self: Description
        :param fav: Description
        :type fav: bool
        """
        self._fav = fav

    @property
    def renderer(self) -> str:
        """
        Docstring for renderer

        :param self: Description
        :return: Description
        :rtype: str
        """
        return self._renderer

    @renderer.setter
    def renderer(self, value: str) -> None:
        self._renderer = value

    @property
    def builder(self) -> int:
        """
        Docstring for builder

        :param self: Description
        :return: Description
        :rtype: int
        """
        return self._builder

    @property
    def tags(self) -> list[str]:
        """
        Docstring for tags

        :param self: Description
        :return: Description
        :rtype: list[str]
        """
        return self._tags

    @tags.setter
    def tags(self, tags: str) -> None:
        """
        Docstring for tags

        :param self: Description
        :param tags: Description
        :type tags: str
        """
        tag = tags.split(",")
        for c in tag:
            c = c.replace(" ", "")
        self._tags = tag

    @property
    def usd(self) -> int:
        """
        Docstring for usd

        :param self: Description
        :return: Description
        :rtype: int
        """
        return self._usd

    @property
    def categories(self) -> list[str]:
        """
        Docstring for categories

        :param self: Description
        :return: Description
        :rtype: list[str]
        """
        return self._cats

    @categories.setter
    def categories(self, cats: str) -> None:
        """
        Docstring for categories

        :param self: Description
        :param cats: Description
        :type cats: str
        """
        cat = cats.split(",")
        for c in cat:
            c = c.replace(" ", "")
        self._cats = cat

    def remove_category(self, cat: str) -> None:
        """
        Docstring for remove_category

        :param self: Description
        :param cat: Description
        :type cat: str
        """
        if cat in self._cats:
            self._cats.remove(cat)

    def rename_category(self, old: str, new: str) -> None:
        """
        Docstring for rename_category

        :param self: Description
        :param old: Description
        :type old: str
        :param new: Description
        :type new: str
        """
        for index, cat in enumerate(self._cats):
            if old == cat:
                self._cats[index] = new

    def set_data(
        self,
        name: str | None,
        cats: str,
        tags: str,
        fav: bool,
        renderer: str | None,
    ) -> None:
        """
        Sets the Material Data to the given parameters

        :param self: Description
        :param name: Description
        :type name: str | None
        :param cats: Description
        :type cats: str
        :param tags: Description
        :type tags: str
        :param fav: Description
        :type fav: bool
        :param renderer: Description
        :type renderer: str | None
        """

        self.categories = cats
        self.tags = tags
        self.fav = fav
        if renderer:
            self._renderer = renderer
        if name:
            self.name = name
        self.set_current_date()
