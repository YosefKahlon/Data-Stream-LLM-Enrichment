from enum import Enum


class Category(str, Enum):
    phishing = "phishing"
    newsletter = "newsletter"
    internal = "internal"
