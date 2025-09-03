from dataclasses import dataclass, field
@dataclass
class LatexConfig:
    main_title: str
    sub_title: dict[str, str] = field(default_factory=dict)

    def add_subtitle(self, key: str, value: str):
        self.sub_title[key] = value

    def remove_subtitle(self, key: str):
        if key in self.sub_title:
            del self.sub_title[key]