import discord
from discord.ext import commands
import itertools

# ----------------------------
# Bot Configuration
# ----------------------------
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ----------------------------
# Betting Program
# ----------------------------
bets = {}
games = {}

# Utility Functions
def implied_probability(odd):
    return 100 / (odd + 100) if odd > 0 else abs(odd) / (abs(odd) + 100)

def decimal_odds(odds):
    if odds > 0:
        return 1 + (odds / 100)
    else:
        return 1 + (100 / abs(odds))

def calculate_kelly_criterion(probability, odds):
    dec_odds = decimal_odds(odds)
    b = dec_odds - 1
    q = 1 - probability
    if b <= 0:
        return 0.0
    kelly_fraction = (b * probability - q) / b
    return max(kelly_fraction, 0.0)

def calculate_units(probability, odds):
    kelly_fraction = calculate_kelly_criterion(probability, odds)
    units = kelly_fraction * 1
    return round(units, 2)

def calculate_combination_units(combo):
    avg_probability = sum(bet['probability'] for _, bet in combo) / len(combo)
    avg_decimal_odds = 1
    for _, bet in combo:
        avg_decimal_odds *= decimal_odds(bet['odds'])
    avg_decimal_odds **= (1 / len(combo))
    avg_odds = (avg_decimal_odds - 1) * 100 if avg_decimal_odds >= 2 else -(100 / (avg_decimal_odds - 1))
    units = calculate_kelly_criterion(avg_probability, avg_odds)
    return round(units, 2)

def calculate_correlation_penalty(bet1, bet2, games):
    penalty = 0.0
    if bet1['team'] == bet2['team']:
        penalty += 0.05
    for game, teams in games.items():
        if bet1['team'] in teams and bet2['team'] in teams:
            penalty += 0.07
    return penalty

def get_top_straight_bets(bets, weight_ev=0.7, weight_prob=0.3):
    straight_bets = []
    for name, bet in bets.items():
        score = (bet['EV'] * weight_ev) + (bet['probability'] * weight_prob)
        units = calculate_units(bet['probability'], bet['odds'])
        straight_bets.append((name, bet, score, units))
    return sorted(straight_bets, key=lambda x: x[2], reverse=True)[:5]

def generate_all_doubles(bets, games):
    valid_doubles = []
    for combo in itertools.combinations(bets.items(), 2):
        valid_doubles.append((combo, sum(bet['EV'] for _, bet in combo), calculate_combination_units(combo)))
    return valid_doubles

def get_balanced_doubles(doubles, weight_ev=0.7, weight_prob=0.3):
    balanced_doubles = []
    for combo, ev, _ in doubles:
        bet1, bet2 = combo[0][1], combo[1][1]
        prob = sum(bet['probability'] for _, bet in combo) / len(combo)
        correlation_penalty = calculate_correlation_penalty(bet1, bet2, games)
        score = (ev * weight_ev) + (prob * weight_prob) - correlation_penalty
        units = calculate_combination_units(combo)
        balanced_doubles.append((combo, score, units))
    return sorted(balanced_doubles, key=lambda x: x[1], reverse=True)[:5]

# ----------------------------
# Bot Commands
# ----------------------------

@bot.event
async def on_ready():
    print(f'{bot.user} is online!')

# Command: Show Top Straight Bets
@bot.command(name='straightbets')
async def straight_bets(ctx):
    if not bets:
        await ctx.send("No bets have been added yet!")
        return
    straight = get_top_straight_bets(bets)
    response = "**Top 5 Straight Bets:**\n"
    for i, (name, bet, score, units) in enumerate(straight, start=1):
        response += f"{i}. **{name}** - EV: {bet['EV']}, Probability: {bet['probability']}, Units: {units}\n"
    await ctx.send(response)

# Command: Show Top Balanced Doubles
@bot.command(name='doubles')
async def balanced_doubles(ctx):
    if not bets:
        await ctx.send("No bets have been added yet!")
        return
    doubles = generate_all_doubles(bets, games)
    balanced = get_balanced_doubles(doubles)
    response = "**Top 5 Balanced Doubles:**\n"
    for i, (combo, score, units) in enumerate(balanced, start=1):
        response += f"{i}. Score: {score}, Units: {units}\n"
        for name, bet in combo:
            response += f"   - {name}: {bet}\n"
    await ctx.send(response)

# Command: Add a Bet
@bot.command(name='addbet')
async def add_bet(ctx, name: str, odds: float, team: str, btype: str, EV: float, probability: float):
    bets[name] = {
        'odds': odds,
        'team': team,
        'type': btype,
        'EV': EV,
        'probability': probability
    }
    await ctx.send(f"✅ Bet '{name}' added successfully!")

# Command: Add a Game
@bot.command(name='addgame')
async def add_game(ctx, game_name: str, team1: str, team2: str):
    games[game_name] = [team1, team2]
    await ctx.send(f"✅ Game '{game_name}' added with teams {team1} and {team2}!")

# Command: Clear Bets and Games
@bot.command(name='clearbets')
async def clear_bets(ctx):
    global bets, games
    bets = {}
    games = {}
    await ctx.send("🧹 All bets and games have been cleared from memory!")

# ----------------------------
# Run the Bot
# ----------------------------
bot.run('MTMyMzgxMjUyMjIzMDQxOTQ5Nw.G2TrL5.nhis_jmFAdBemEyz8fiCdhTbdbEDJQrJm3pDvU')
