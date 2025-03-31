import csv
import random
from datetime import datetime, timedelta

# ----------------------------
# Helper Functions
# ----------------------------

def compute_age(birth_date, current_date):
    """
    Calculates a user's age based on their birth date and the current session date.
    This ensures that age changes over time during the simulation.
    """
    age = current_date.year - birth_date.year
    if (current_date.month, current_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age

def approximate_pushup_capacity(age, weight, gender):
    """
    Estimates a baseline push-up count based on user demographics.
    Younger, lighter users tend to start stronger.
    Includes small random variation for realism.
    """
    if gender == 'Male':
        base = 10
        if age < 20:
            base += 5
        elif age > 40:
            base -= 2
        elif age > 60:
            base -= 4

        if weight < 60:
            base += 3
        elif weight > 80:
            base -= 2
        elif weight > 100:
            base -= 4
    else:  # Female
        base = 5
        if age < 20:
            base += 2
        elif age > 40:
            base -= 1
        elif age > 60:
            base -= 2

        if weight < 50:
            base += 2
        elif weight > 70:
            base -= 1
        elif weight > 90:
            base -= 2

    # Add small random variation
    base += random.randint(-2, 2)
    return max(base, 1)

def update_pushups(pushups_prev, gender, plateau_state):
    """
    Simulates realistic push-up progression:
    - Improvements slow down as push-up count increases.
    - Plateaus and regressions are introduced to prevent perfectly linear growth.
    - Adds more realistic variability in progress over time.
    """

    # If currently plateauing, maintain same pushup count
    if plateau_state['count'] > 0:
        plateau_state['count'] -= 1
        return pushups_prev

    # Determine expected increment based on current performance
    if gender == 'Male':
        if pushups_prev < 20:
            increment = random.uniform(0.6, 1.3)
        elif pushups_prev < 40:
            increment = random.uniform(0.4, 1.0)
        elif pushups_prev < 60:
            increment = random.uniform(0.2, 0.65)
        else:
            increment = random.uniform(0.1, 0.55)
    else: # Female
        if pushups_prev < 20:
            increment = random.uniform(0.4, 1.0)
        elif pushups_prev < 40:
            increment = random.uniform(0.3, 0.7)
        elif pushups_prev < 60:
            increment = random.uniform(0.1, 0.55)
        else:
            increment = random.uniform(0.1, 0.3)

    # Introduce chance of no improvement or slight regression
    chance_bad_day = random.random()
    if chance_bad_day < 0.25:
        # Single bad session
        increment = random.uniform(-1.0, 0.3)
    elif chance_bad_day < 0.35:
        # Start a plateau (1–4 sessions)
        plateau_state['count'] = random.randint(1, 4)
        increment = 0

    new_value = pushups_prev + increment
    return max(1, round(new_value))

def update_weight(weight_prev):
    """
    Introduces minor weight changes over time.
    Simulates realistic day-to-day fluctuations.
    """
    if random.random() < 0.10:
        change = random.uniform(-0.5, 0.5)
        new_weight = max(40.0, weight_prev + change)
        return round(new_weight, 2)
    return weight_prev

# ----------------------------
# Main Dataset Generation
# ----------------------------

def generate_dataset(filename="pushup_data.csv", num_users=50, sessions_per_user=500):
    """
    Generates a synthetic push-up dataset:
    - Each user trains over 500 sessions.
    - Push-up count improves realistically over time.
    - Includes features like gender, age, weight, frequency of training, etc.
    - Accounts for bad days, plateaus, and fluctuations in weight.
    - Saves output as a CSV file for use in analytics or ML model training.
    """
    start_date = datetime(2023, 1, 1)

    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "weight", "age", "gender", "pushups", "date", "session_id", "frequency"])

        for user_id in range(num_users):
            gender = random.choice(["Male", "Female"])
            initial_age = random.randint(15, 70)

            # Assign starting weight based on gender
            weight = round(random.uniform(55, 110), 2) if gender == "Male" else round(random.uniform(45, 90), 2)

            # Determine birth date based on initial age
            birth_year = start_date.year - initial_age
            birth_date = datetime(birth_year, 1, 1)

            # Estimate starting pushup performance
            current_pushups = approximate_pushup_capacity(initial_age, weight, gender)

            # Random training frequency (sessions/week)
            sessions_per_week = random.randint(1, 3)

            current_date = start_date
            session_id = 1
            plateau_state = {'count': 0}  # For tracking session plateaus

            for _ in range(sessions_per_user):
                current_age = compute_age(birth_date, current_date)

                # Write the current session row to the CSV
                writer.writerow([
                    user_id,
                    weight,
                    current_age,
                    gender,
                    current_pushups,
                    current_date.strftime("%Y-%m-%d"),
                    session_id,
                    sessions_per_week
                ])

                # Update pushups and weight for the next session
                current_pushups = update_pushups(current_pushups, gender, plateau_state)
                weight = update_weight(weight)

                # Determine next session date
                avg_days = 7 // sessions_per_week
                day_variation = random.choice([-1, 0, 1])
                days_between_sessions = max(1, avg_days + day_variation)
                current_date += timedelta(days=days_between_sessions)
                session_id += 1

    print(f"Dataset '{filename}' generated with {num_users} users, each with {sessions_per_user} sessions.")

if __name__ == "__main__":
    generate_dataset()
