import math, time
from brownie import Contract
import time

from tests.conftest import yveCrv


def test_harvest_trigger(Strategy, accounts, live_strat, token, yveCrv, whale_yvecrv, eth_whale, vault, strategy, strategist, amount, user, crv3, chain, whale_3crv, gov):
    new_strategy = strategist.deploy(Strategy, vault)
    vault.migrateStrategy(live_strat, new_strategy, {"from":gov})
    strategy = new_strategy
    gasOracle = Contract("0xb5e1CAcB567d98faaDB60a1fD4820720141f064F")
    gasOracle.setMaxAcceptableBaseFee(2000 * 1e9, {"from": vault.management()})
    crv3.transfer(strategy, 10e20, {"from": whale_3crv})
    # assert not strategy.harvestTrigger(1e9)
    yveCrv.transfer(strategy, 1e18, {"from": whale_yvecrv})
    assert strategy.harvestTrigger(1e9)

def test_should_claim(accounts, token, Strategy, live_strat, yveCrv, whale_yvecrv, eth_whale, vault, strategy, strategist, amount, user, crv3, chain, whale_3crv, gov):
    new_strategy = strategist.deploy(Strategy, vault)
    vault.migrateStrategy(live_strat, new_strategy, {"from":gov})
    strategy = new_strategy
    assert strategy.shouldClaim()
    strategy.toggleShouldClaim({"from": vault.management()})
    assert not strategy.shouldClaim()

def test_operation(accounts, Strategy, trade_factory, ymechs_safe, live_strat, token, eth_whale, vault, strategy, strategist, amount, user, crv3, chain, whale_3crv, gov):
    new_strategy = strategist.deploy(Strategy, vault)
    vault.migrateStrategy(live_strat, new_strategy, {"from":gov})
    strategy = new_strategy
    vault_before = token.balanceOf(vault)
    strat_before = token.balanceOf(strategy)
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount + vault_before
    trade_factory.grantRole(trade_factory.STRATEGY(), new_strategy.address, {"from": ymechs_safe, "gas_price": "0 gwei"})
    new_strategy.setTradeFactory(trade_factory.address, {"from": gov})
    strategy.harvest({'from': strategist})

def test_change_debt(gov, Strategy, live_strat, token, trade_factory, vault, ymechs_safe, strategy, strategist, amount, user):
    new_strategy = strategist.deploy(Strategy, vault)
    vault.migrateStrategy(live_strat, new_strategy, {"from":gov})
    trade_factory.grantRole(trade_factory.STRATEGY(), new_strategy.address, {"from": ymechs_safe, "gas_price": "0 gwei"})
    new_strategy.setTradeFactory(trade_factory.address, {"from": gov})
    strategy = new_strategy
    # Deposit to the vault and harvest
    before = strategy.estimatedTotalAssets()
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    strategy.harvest({"from":strategist})
    after = strategy.estimatedTotalAssets()
    assert after < before
    vault.updateStrategyDebtRatio(strategy.address, 10_000, {"from": gov})
    strategy.harvest({"from":strategist})
    assert after < strategy.estimatedTotalAssets()

def test_migrate(Strategy, accounts, live_strat, token, yveCrv, whale_yvecrv, eth_whale, vault, strategy, strategist, amount, user, crv3, chain, whale_3crv, gov):
    new_strategy = strategist.deploy(Strategy, vault)
    vault.migrateStrategy(live_strat, new_strategy, {"from":gov})
    strategy = new_strategy
    old_bal1 = token.balanceOf(strategy)
    old_bal2 = crv3.balanceOf(strategy)
    new = strategist.deploy(Strategy, vault)
    vault.migrateStrategy(strategy, new, {'from':gov})
    new_bal1 = token.balanceOf(new)
    new_bal2 = crv3.balanceOf(new)
    assert new_bal1 > 0
    assert old_bal1 == new_bal1
    assert old_bal2 == new_bal2