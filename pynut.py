# === Tech Summary ===
# This block imports all required libraries:
# - streamlit: for building web interfaces
# - requests: for making HTTP API calls
# - pandas: for tabular data handling using DataFrames
# - numpy: for numerical and array computations
# - matplotlib.pyplot: for static data visualization (e.g., charts)
# - json: for encoding and decoding JSON objects
# - os: for accessing the operating system’s file paths and environment
# =====================

import streamlit as st             # Build web-based front-end interface
import requests                    # Send HTTP requests (e.g., API calls)
import pandas as pd                # Handle tabular data (commonly with DataFrame)
import numpy as np                 # Numerical computing with array and matrix support
import matplotlib.pyplot as plt    # Plotting library for static visualizations
import json                        # Parse and store JSON data
import os                          # OS-level operations like file paths

API_KEY = "nqj9Kh3QVKwI4AFfuwGddoSOQznWReylbYLFynzU" # This is the API key to the USDA API

# === Tech Summary ===
# This function queries the USDA FoodData Central API to search for branded food items.
# It accepts a search keyword, an API key, and the max number of results to return (default: 100).
# If the API call is successful, it extracts and returns a list of FDC (FoodData Central) IDs.
# If the request fails (non-200 response), it logs the error and returns an empty list.
# =====================

def search_usda_foods(query, api_key, max_results=100):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"  # API endpoint for USDA food search

    params = {                              # Define query parameters
        "api_key": api_key,                 # API key for authentication
        "query": query,                     # Search keyword
        "pageSize": max_results,            # Max number of results to return
        "dataType": ["Branded"]             # Restrict to branded food items
    }

    response = requests.get(url, params=params)          # Make HTTP GET request

    if response.status_code != 200:                      # Handle failed request
        st.error(f"Search error {response.status_code}") # Display error in Streamlit UI
        return []                                        # Return empty list on failure

    return [food["fdcId"] for food in                   # Extract list of food IDs from JSON response
            response.json().get("foods", [])]

# === Tech Summary ===
# This function sends a POST request to the USDA API to fetch detailed information
# for a list of food items using their FDC IDs.
# It sets appropriate JSON headers, includes the FDC ID list in the request payload,
# and appends the API key as a parameter.
# On success (HTTP 200), it returns the parsed JSON response; otherwise, it returns an empty list.
# =====================

def fetch_multiple_foods(fdc_ids, api_key):
    
    url = "https://api.nal.usda.gov/fdc/v1/foods"              # API endpoint for batch food lookup

    headers = {"Content-Type": "application/json"}             # Specify JSON content in POST header
    payload = {"fdcIds": fdc_ids}                              # Payload includes list of food IDs
    params = {"api_key": api_key}                              # API key passed as URL parameter

    response = requests.post(                                  # Send POST request with payload & headers
        url, headers=headers, json=payload, params=params
    )

    return response.json() if response.status_code == 200 else []  # Return JSON data or empty list
    
# === Tech Summary ===
# This function extracts a standardized set of nutritional information from a list of food items.
# It converts USDA food records into a pandas DataFrame with key nutrient values.
# - It first maps USDA nutrient names to custom column labels (e.g., "Protein (g)", "Sodium (mg)").
# - For each food item, it extracts relevant nutrient values and fills in missing ones with 0.
# - Returns a structured DataFrame with rows representing food items and columns for nutrients.
# =====================

def extract_nutrients_df(food_list):
    
    key_nutrients = {                                       # Map USDA nutrient names to display labels
        "Energy": "Calories",
        "Protein": "Protein (g)",
        "Total lipid (fat)": "Fat (g)",
        "Carbohydrate, by difference": "Carbs (g)",
        "Sugars, total including NLEA": "Sugar (g)",
        "Total Sugars": "Sugar (g)",
        "Fiber, total dietary": "Fiber (g)",
        "Sodium, Na": "Sodium (mg)"
    }

    radar_labels = [                                        # Nutrient labels to ensure column consistency
        "Calories", "Protein (g)", "Fat (g)", "Carbs (g)",
        "Sugar (g)", "Fiber (g)", "Sodium (mg)"
    ]

    records = []                                            # Initialize list to hold each row of data

    for food in food_list:
        row = {
            "Food": food.get("description", ""),            # Extract food name
            "FDC ID": food.get("fdcId", ""),                # Unique ID
            "Brand": food.get("brandOwner", "")             # Brand information
        }

        for item in food.get("foodNutrients", []):          # Loop through each nutrient in food item
            name = item.get("nutrient", {}).get("name", "") # Get nutrient name
            if name in key_nutrients:
                row[key_nutrients[name]] = float(item.get("amount", 0))  # Save amount if it's in key list

        for label in radar_labels:                          # Ensure all radar labels are present
            row.setdefault(label, 0.0)                       # Default to 0 if not extracted

        records.append(row)                                 # Append complete row to list

    return pd.DataFrame(records)        

# === Tech Summary ===
# This function estimates Total Energy Expenditure (TEE) using different formulas 
# based on gender, age group, and activity level.
# - For infants (age ≤ 2), simplified formulas are used.
# - For children and adults, age-specific equations (from USDA or academic references)
#   are used for each activity level: inactive, low active, and active.
# - The result is a daily TEE value in kcal/day.
# =====================

def calculate_tee(gender, age, height, weight, activity_level):
    if gender == 'male':
        if age <= 2:
            # Infant male TEE formula
            return -716.45 - (1.00 * age) + (17.82 * height) + (15.06 * weight)

        elif age < 19:
            # Boys aged 3–18, equations by activity level
            if activity_level == 'inactive':
                return -447.51 - 3.68 * age + 13.01 * height + 13.15 * weight
            elif activity_level == 'low active':
                return 19.12 + 3.68 * age + 8.62 * height + 20.28 * weight
            elif activity_level == 'active':
                return -388.19 + 3.68 * age + 12.66 * height + 20.46 * weight
            else:  # very active or unknown
                return -671.75 + 3.68 * age + 15.38 * height + 23.25 * weight

        else:
            # Adult male (≥19 years old), equations by activity level
            if activity_level == 'inactive':
                return 753.07 - 10.83 * age + 6.50 * height + 14.10 * weight
            elif activity_level == 'low active':
                return 581.47 - 10.83 * age + 8.30 * height + 14.94 * weight
            elif activity_level == 'active':
                return 1004.82 - 10.83 * age + 6.52 * height + 15.91 * weight
            else:
                return -517.88 - 10.83 * age + 15.61 * height + 19.11 * weight

    else:  # female
        if age <= 2:
            # Infant female TEE formula
            return -69.15 + 80.0 * age + 2.65 * height + 54.15 * weight

        elif age < 19:
            # Girls aged 3–18
            if activity_level == 'inactive':
                return 55.59 - 22.25 * age + 8.43 * height + 17.07 * weight
            elif activity_level == 'low active':
                return -297.54 - 22.25 * age + 12.77 * height + 14.73 * weight
            elif activity_level == 'active':
                return -189.55 - 22.25 * age + 11.74 * height + 18.34 * weight
            else:
                return -709.59 - 22.25 * age + 18.22 * height + 14.25 * weight

        else:
            # Adult female (≥19 years old)
            if activity_level == 'inactive':
                return 584.90 - 7.01 * age + 5.72 * height + 11.71 * weight
            elif activity_level == 'low active':
                return 575.77 - 7.01 * age + 6.60 * height + 12.14 * weight
            elif activity_level == 'active':
                return 710.25 - 7.01 * age + 6.54 * height + 12.34 * weight
            else:
                return 511.83 - 7.01 * age + 9.07 * height + 12.56 * weight
                
# === Tech Summary ===
# This function calculates the target intake (in grams) of macronutrients
# per meal based on total daily energy expenditure (TEE).
# Assumptions:
# - 40% of calories from protein, 30% from fat, 30% from carbs
# - Protein and carbs: 4 kcal/g; fat: 9 kcal/g
# - Daily intake is divided equally into 3 meals
# =====================

def compute_target_macros_per_meal(tee):
    return {
        "Protein (g)": tee * 0.4 / 4 / 3,   # 40% of calories → divide by 4 kcal/g → 3 meals
        "Fat (g)":     tee * 0.3 / 9 / 3,   # 30% of calories → divide by 9 kcal/g → 3 meals
        "Carbs (g)":   tee * 0.3 / 4 / 3    # 30% of calories → divide by 4 kcal/g → 3 meals
    }
    
# === Tech Summary ===
# This function scores food records in a DataFrame based on how closely they match
# the target macro and calorie goals for one meal.
# - Each nutrient has its own scoring function:
#   - Calories/Fat/Carbs: penalized if over target
#   - Protein: capped at 1 when exceeding target
# - Weights for total score depend on the selected goal (muscle_gain or fat_loss)
# - Final output is the same DataFrame with added score columns, sorted by Total Score
# =====================

def score_menu(df, targets, tee, goal):
    # Helper: score = x / t if under target, else penalize
    def bounded_score(x, t): return min(x / t, 1)

    # Penalize over-target macros with a decreasing function (2 - x/t), min 0
    def penalized_score(x, t): return max(0, 2 - x / t) if x > t else x / t

    # Individual nutrient scores
    df["Calories Score"] = df["Calories"].apply(lambda x: penalized_score(x, tee))
    df["Protein Score"]  = df["Protein (g)"].apply(lambda x: bounded_score(x, targets["Protein (g)"]))
    df["Fat Score"]      = df["Fat (g)"].apply(lambda x: penalized_score(x, targets["Fat (g)"]))
    df["Carbs Score"]    = df["Carbs (g)"].apply(lambda x: penalized_score(x, targets["Carbs (g)"]))

    # Different weights for different goals
    weights = {
        "muscle_gain": [0.2, 0.4, 0.2, 0.2],  # Emphasize protein for bulking
        "fat_loss":    [0.3, 0.4, 0.3, 0.2]   # Balance between calorie and protein
    }[goal]

    # Weighted total score = sum of nutrient scores × weights
    df["Total Score"] = (
        df["Calories Score"] * weights[0] +
        df["Protein Score"]  * weights[1] +
        df["Fat Score"]      * weights[2] +
        df["Carbs Score"]    * weights[3]
    )

    return df.sort_values("Total Score", ascending=False)  # Highest score first

# === Tech Summary ===
# This function plots a radar chart for a single food item's nutrient values.
# Each nutrient is normalized against standard daily values (DV) for adults.
# - Uses matplotlib to draw a circular radar chart with 7 nutrients
# - Scales values between 0 and 1 (as % of daily recommended intake)
# - Fills the area to show nutrient density at a glance
# - Outputs the plot directly into Streamlit via st.pyplot()
# =====================

def plot_radar_chart(row):
    labels = [                                       # Nutrients to include in the radar chart
        "Calories", "Protein (g)", "Fat (g)", "Carbs (g)",
        "Sugar (g)", "Fiber (g)", "Sodium (mg)"
    ]

    daily = {                                        # Daily recommended values for each nutrient
        "Calories": 2000, "Protein (g)": 50, "Fat (g)": 78,
        "Carbs (g)": 300, "Sugar (g)": 50, "Fiber (g)": 28, "Sodium (mg)": 2300
    }

    values = [row[l] / daily[l] for l in labels]     # Normalize each nutrient by daily value
    values += [values[0]]                            # Close the radar shape by repeating the first value

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist() + [0]  # Radar chart angles

    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))  # Create polar (radar) plot
    ax.plot(angles, values)                          # Draw the outline
    ax.fill(angles, values, alpha=0.25)              # Fill the area with transparency

    ax.set_xticks(angles[:-1])                       # Set axis ticks
    ax.set_xticklabels(labels, fontsize=8)           # Set tick labels (nutrients)
    ax.set_ylim(0, 1)                                # Set radial axis from 0 to 100% of DV
    ax.set_title(row["Food"], y=1.1)                 # Title = food name

    st.pyplot(fig)                                   # Render plot in Streamlit

# === Tech Summary ===
# This function estimates an individual's average speed (in km/h or mph) for a given activity,
# adjusted based on their BMI and age.
# - A base speed is defined for each activity type.
# - If BMI > 25 (overweight), speed is reduced by 10%.
# - If age > 40, speed is further reduced by 5%.
# - Returns the adjusted speed rounded to 2 decimal places.
# =====================

def estimate_speed_bmi_age(activity, bmi, age):
    base_speeds = {                        # Define default speeds by activity type
        "Running": 9.0,
        "Swimming": 3.0,
        "Cycling": 15.0,
        "Walking": 5.0
    }

    speed = base_speeds.get(activity, 5.0) # Use default of 5.0 if activity is unknown

    if bmi > 25:                           # Reduce speed by 10% if overweight
        speed *= 0.9

    if age > 40:                           # Reduce speed by 5% if older
        speed *= 0.95

    return round(speed, 2)                # Round final result to 2 decimal places
    
# === Tech Summary ===
# This function estimates how long and how far a person needs to exercise to burn a given number of calories,
# considering BMI and age adjustments.
# - Takes in a calorie target, user's BMI, and age.
# - For each activity, computes:
#   - Time required (in minutes)
#   - Estimated speed (adjusted for BMI and age)
#   - Total distance covered in km
# - Returns a dictionary mapping each activity to its estimated time, distance, and speed.
# =====================

def calories_to_exercise_with_distance(calories, bmi, age):
    activities = {                            # Activity name and estimated kcal burned per minute
        "Running": 10,
        "Swimming": 14,
        "Cycling": 8,
        "Walking": 4
    }

    result = {}

    for activity, kcal_per_min in activities.items():
        minutes = calories / kcal_per_min     # Time needed to burn target calories
        speed = estimate_speed_bmi_age(activity, bmi, age)  # Adjusted speed (km/h)
        distance = (minutes / 60) * speed     # Convert time to hours × speed = distance

        result[activity] = {
            "time_min": round(minutes),       # Time in minutes
            "distance_km": round(distance, 2),# Distance in km, rounded to 2 decimals
            "speed_kmh": speed                # Raw speed value
        }

    return result
    
# === Tech Summary ===
# This function calculates Basal Metabolic Rate (BMR) using the Mifflin-St Jeor equation.
# BMR represents the number of calories required to maintain basic bodily functions at rest.
# Formula:
# - Male:    10 × weight + 6.25 × height − 5 × age + 5
# - Female:  10 × weight + 6.25 × height − 5 × age − 161
# Units:
# - weight: in kilograms (kg)
# - height: in centimeters (cm)
# - age: in years
# =====================

def calculate_bmr(gender, age, height, weight):
    if gender.lower() == "male":
        return 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161
        return 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)



