import pandas as pd
import numpy as np
import random

IN_FILE = "input.xlsx"
OUT_FILE = "output.xlsx"
QUOTA = {
    "Badminton (C)": {
        "MALE": 10,
        "FEMALE": 10
    },
    "Handball (G)": {
        "MALE": None,
        "FEMALE": 20
    },
    "Ultimate Frisbee (B)": {
        "MALE": 18,
        "FEMALE": None
    },
    "Pickleball (C)": {
        "MALE": 5,
        "FEMALE": 5
    }
}


def read_file(filename):
    df = pd.read_excel(filename, engine='openpyxl')
    df = df.iloc[:, :7]
    return df


def find_lowest_count_sport(df, gender):
    counts = {s: len(df.loc[(df["result"] == s) & (
        df.iloc[:, 3] == gender)]) for s in list(QUOTA.keys())}
    counts = dict(sorted(counts.items(), key=lambda x: x[1]))
    for s in counts.keys():
        if QUOTA[s][gender]:
            if counts[s] < QUOTA[s][gender]:
                return s
        else:
            continue


def clean_data(df, genders):
    # clean data

    # filter out invalid profiles
    o_shape = df.shape
    df = df[
        (df.iloc[:, :3].notnull().all(axis=1))
        &
        (df.iloc[:, 3].isin(genders))
    ]
    lines_filtered = o_shape[0] - df.shape[0]
    if lines_filtered:
        print(f"warning: {lines_filtered} lines removed during cleaning...")

    # clean invalid choices
    choice_cols = df.columns.tolist()[4:]
    sports = [s.lower() for s in list(QUOTA.keys())] + \
        ["No Preference".lower()]
    # change invalid to NaN, and print a warning
    for i in range(len(df)):
        for choice in choice_cols:
            if (str(df.iloc[i][choice]).lower() not in sports):
                print(
                    f"warning: invalid choice L{i+1}: {list(df.iloc[i])}, converting to no preference.")
                df.at[i, choice] = "No Preference"

    # ensuring that "No Preference" is sequential
    for i in range(len(df)):
        no_pref_boos = (df.iloc[i, 3:] == "No Preference")
        if no_pref_boos.any():
            if not (np.sort(no_pref_boos) == no_pref_boos).all():
                print(
                    f"Error: incorrect no pref order L{i+1}: {list(df.iloc[i])}")
                exit(1)

    return df


def selection(df):
    choice_cols = df.columns.tolist()[4:7]

    for j in range(len(choice_cols)):
        choice = choice_cols[j]

        waiting = []
        count = 0

        while df["result"].isna().any() and (count < df.shape[0]):
            student = df.sample(n=1, replace=False)
            count += 1

            if not student["result"].isna().bool():
                # skip if student is selected
                continue

            sport = student[choice].iloc[0]
            gender = student.iloc[0, 3]

            # no preference
            if sport == "No Preference":
                waiting.append(student)
                continue

            if not QUOTA[sport][gender]:
                continue
            elif len(df.loc[(df["result"] == sport) & (df.iloc[:, 3] == gender)]) < QUOTA[sport][gender]:
                # quota not maxed out yet
                df.at[student.index, "result"] = sport
            else:
                waiting.append(student)

        # clear waiting list
        for student in waiting:
            if not df["result"].isna().any():
                break

            gender = student.iloc[0, 3]

            if student[choice].iloc[0] == "No Preference":
                # add student to sport with lowest count
                sport = find_lowest_count_sport(df, gender)
                df.at[student.index, "result"] = sport

            else:
                choice_index = j+1
                if j+1 >= len(choice_cols):
                    continue

                # select the student's next choice
                sport = student[choice_cols[choice_index]].iloc[0]
                if sport == "No Preference":
                    continue

                if len(df.loc[(df["result"] == sport) & (df.iloc[:, 3] == gender)]) < QUOTA[sport][gender]:
                    df.at[student.index, "result"] = sport

    return df


def check_quota_filled(df, genders):
    counts = {
        s: {g: len(df.loc[(df["result"] == s) & (df.iloc[:, 3] == g)])
            for g in genders}
        for s in list(QUOTA.keys())
    }

    quota_met = []
    for s in QUOTA.keys():
        for g in QUOTA[s].keys():
            if QUOTA[s][g]:
                quota_met.append(QUOTA[s][g] == counts[s][g])
    return any(quota_met)


def main(input_file: str, output_file: str):

    GENDER = ["MALE", "FEMALE"]
    SELECT_MAX = 10

    df = read_file(input_file)
    df = clean_data(df, GENDER)
    df["result"] = np.nan

    selection_count = 0
    while (not check_quota_filled(df, GENDER)) \
            and (selection_count < SELECT_MAX):
        # keep selecting till quota is filled
        df = selection(df)
        selection_count += 1

    # writing output
    df.to_excel(output_file, index=False)


if __name__ == '__main__':
    main(IN_FILE, OUT_FILE)
