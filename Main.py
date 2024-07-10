

import random
from negmas.outcomes import Outcome
from negmas.sao import ResponseType, SAONegotiator, SAOResponse, SAOState

class Group10(SAONegotiator):
    """
    Implements a hybrid negotiation strategy with dynamic adjustments and strategic counter-offers.
    """
    rational_outcomes = []
    partner_reserved_value = 0
    last_opponent_offer = None
    last_own_offer = None
    acceptance_threshold = None

    def on_preferences_changed(self, changes):
        all_outcomes = list(self.nmi.outcome_space.enumerate_or_sample())
        self.acceptance_threshold = self.ufun.reserved_value * 1.2
        self.rational_outcomes = [
            outcome for outcome in all_outcomes if self.ufun(outcome) > self.ufun.reserved_value
        ]
        self.partner_reserved_value = self.ufun.reserved_value

    def __call__(self, state: SAOState) -> SAOResponse:
        offer = state.current_offer
        self.update_partner_reserved_value(state)
        self.update_acceptance_threshold(state, offer)
        self.last_opponent_offer = offer

        if self.acceptance_strategy(state):
            return SAOResponse(ResponseType.ACCEPT_OFFER, offer)
        else:
            counter_offer = self.bidding_strategy(state)
            self.last_own_offer = counter_offer
            return SAOResponse(ResponseType.REJECT_OFFER, counter_offer)

    def update_acceptance_threshold(self, state, offer):
        time_left = 1 - state.relative_time
        if offer and self.ufun(offer) > self.ufun(self.last_opponent_offer):
            self.acceptance_threshold *= 1.0  
        elif time_left < 0.3:
            self.acceptance_threshold *= 0.85  

    def acceptance_strategy(self, state: SAOState) -> bool:
        current_offer_utility = self.ufun(state.current_offer)
        if self.last_opponent_offer:
            improvement = self.ufun(state.current_offer) > self.ufun(self.last_opponent_offer)
        if improvement:
            self.acceptance_threshold *= 0.95
        return current_offer_utility >= self.acceptance_threshold

    def bidding_strategy(self, state: SAOState) -> Outcome | None:
        if self.ufun is None:
            return None
        if state.relative_time < 0.2:
            return max(self.rational_outcomes, key=self.ufun)
        if self.last_opponent_offer and self.ufun(self.last_opponent_offer) < self.ufun(self.last_own_offer):
            return self.last_own_offer
        else:
            improved_offers = [o for o in self.rational_outcomes if self.ufun(o) > self.ufun(self.last_opponent_offer)]
            return random.choice(improved_offers) if improved_offers else random.choice(self.rational_outcomes)


    def update_partner_reserved_value(self, state: SAOState):
        offer = state.current_offer
        if offer is not None:
            opponent_utility = self.opponent_ufun(offer)
            self.partner_reserved_value = min(opponent_utility, self.partner_reserved_value)

if __name__ == "__main__":
    from helpers.runner import run_a_tournament
    run_a_tournament(Group10, small=True)