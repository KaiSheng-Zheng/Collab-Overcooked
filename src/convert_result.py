import os
from argparse import ArgumentParser

import pandas as pd


level_1 = [
    "baked_bell_pepper",
    "baked_sweet_potato",
    "boiled_egg",
    "boiled_mushroom",
    "boiled_sweet_potato",
]

level_2 = [
    "baked_potato_slices",
    "baked_pumpkin_slices",
    "boiled_corn_slices",
    "boiled_green_bean_slices",
    "boiled_potato_slices",
]

level_3 = [
    "baked_bell_pepper_soup",
    "baked_carrot_soup",
    "baked_mushroom_soup",
    "baked_potato_soup",
    "baked_pumpkin_soup",
]

level_4 = [
    "sliced_bell_pepper_and_corn_stew",
    "sliced_bell_pepper_and_lentil_stew",
    "sliced_eggplant_and_chickpea_stew",
    "sliced_pumpkin_and_chickpea_stew",
    "sliced_zucchini_and_chickpea_stew",
]

level_5 = [
    "mashed_broccoli_and_bean_patty",
    "mashed_carrot_and_chickpea_patty",
    "mashed_cauliflower_and_lentil_patty",
    "mashed_potato_and_pea_patty",
    "mashed_sweet_potato_and_bean_patty",
]

level_6 = [
    "potato_carrot_and_onion_patty",
    "romaine_lettuce_pea_and_tomato_patty",
    "sweet_potato_spinach_and_mushroom_patty",
    "taro_bean_and_bell_pepper_patty",
    "zucchini_green_pea_and_onion_patty",
]

levels = {
    "level_1": level_1,
    "level_2": level_2,
    "level_3": level_3,
    "level_4": level_4,
    "level_5": level_5,
    "level_6": level_6,
}


def parse_list_argument(value):
    if not value:
        return []
    return [item.strip() for item in value.replace(",", " ").split() if item.strip()]


def get_level(order):
    for level_name, orders in levels.items():
        if order in orders:
            return level_name
    return None


def main(args):
    input_path = os.path.join(args.eval_result_dir, args.input)
    output_path = os.path.join(args.eval_result_dir, args.output)

    data = pd.read_csv(input_path)

    models = parse_list_argument(args.models)
    if models:
        data = data[data["model"].isin(models)]

    data["level"] = data["order"].apply(get_level)
    data = data.dropna(subset=["level"])

    columns_to_average = [
        col for col in data.columns if col not in ["model", "order", "level"]
    ]
    data[columns_to_average] = data[columns_to_average].apply(
        pd.to_numeric, errors="coerce"
    )

    grouped_data = data.groupby(["model", "level"])[columns_to_average].mean()
    grouped_data.to_csv(output_path, sep=",")
    print(f"Converted result saved to {output_path}.")


if __name__ == "__main__":
    parser = ArgumentParser(description="Convert per-task metrics to per-level means.")
    parser.add_argument(
        "--eval_result_dir",
        type=str,
        default="eval_result",
        help="Directory containing evaluation CSV files",
    )
    parser.add_argument(
        "--input",
        type=str,
        default="statistics_data.csv",
        help="Input CSV filename under eval_result_dir",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="converted_data.csv",
        help="Output CSV filename under eval_result_dir",
    )
    parser.add_argument(
        "--models",
        type=str,
        default=None,
        help="Optional comma or space separated model names to include",
    )
    main(parser.parse_args())
