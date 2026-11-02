"""Synthetic boundary mutants (known to the benchmark author)."""
from dataclasses import dataclass
from random import Random
from typing import Any, Callable

@dataclass(frozen=True)
class Case:
    name: str
    description: str
    reference: Callable[[Any], Any]
    mutant: Callable[[Any], Any]
    random_input: Callable[[Random], Any]
    edge_inputs: tuple[Any, ...]

def leap_year(y: int) -> bool:
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)
def leap_year_bug(y: int) -> bool:
    return y % 4 == 0
def can_withdraw(arg: tuple[int,int]) -> bool:
    balance, amount = arg
    return 0 <= amount <= balance
def can_withdraw_bug(arg: tuple[int,int]) -> bool:
    balance, amount = arg
    return 0 <= amount < balance
def free_shipping(cents: int) -> bool:
    return cents >= 5000
def free_shipping_bug(cents: int) -> bool:
    return cents > 5000
def exists(arg: tuple[tuple[int,...],int]) -> bool:
    values, target = arg
    return target in values
def exists_bug(arg: tuple[tuple[int,...],int]) -> bool:
    values, target = arg
    return target in values[:-1]
def password_ok(length: int) -> bool:
    return 8 <= length <= 64
def password_ok_bug(length: int) -> bool:
    return 8 < length < 64
def is_prime(n: int) -> bool:
    if n < 2: return False
    return all(n % i for i in range(2, int(n**0.5)+1))
def is_prime_bug(n: int) -> bool:
    return all(n % i for i in range(2, int(n**0.5)+1))
def random_search_arg(rng: Random) -> tuple[tuple[int,...],int]:
    values = tuple(sorted(rng.sample(range(-500,501), rng.randint(3,12))))
    return values, rng.randint(-500,500)

CASES = (
    Case("annee_bissextile", "Exception siecles", leap_year, leap_year_bug,
        lambda rng: rng.randint(1800,2200), (1900,2000,2100,2400,1800,2200)),
    Case("retrait_bancaire", "Amount equals balance", can_withdraw, can_withdraw_bug,
        lambda rng: (rng.randint(0,1000),rng.randint(0,1000)),
        ((0,0),(1,1),(100,100),(10,9),(10,11),(0,1))),
    Case("livraison_gratuite", "Inclusive threshold", free_shipping, free_shipping_bug,
        lambda rng: rng.randint(0,10000), (4999,5000,5001,0,10000,4998)),
    Case("recherche_liste", "Last item skipped", exists, exists_bug, random_search_arg,
        (((1,2,3),3),((-1,0,7),7),((1,2,3),1),((1,2,3),4))),
    Case("mot_de_passe", "Inclusive minimum/maximum", password_ok, password_ok_bug,
        lambda rng: rng.randint(0,100), (7,8,9,63,64,65)),
    Case("nombre_premier", "1 is not prime", is_prime, is_prime_bug,
        lambda rng: rng.randint(1,1000), (0,1,2,3,4,9)),
)
