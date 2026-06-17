import os
import json
import time
import pandas as pd
from argparse import ArgumentParser


DEFAULT_MODELS = ["gpt-4o"]

DEFAULT_ORDERS = [
    "baked_bell_pepper",
    "baked_sweet_potato",
    "boiled_egg",
    "boiled_mushroom",
    "boiled_sweet_potato",
    "baked_potato_slices",
    "baked_pumpkin_slices",
    "boiled_corn_slices",
    "boiled_green_bean_slices",
    "boiled_potato_slices",
    "baked_bell_pepper_soup",
    "baked_carrot_soup",
    "baked_mushroom_soup",
    "baked_potato_soup",
    "baked_pumpkin_soup",
    "sliced_bell_pepper_and_corn_stew",
    "sliced_bell_pepper_and_lentil_stew",
    "sliced_eggplant_and_chickpea_stew",
    "sliced_pumpkin_and_chickpea_stew",
    "sliced_zucchini_and_chickpea_stew",
    "mashed_broccoli_and_bean_patty",
    "mashed_carrot_and_chickpea_patty",
    "mashed_cauliflower_and_lentil_patty",
    "mashed_potato_and_pea_patty",
    "mashed_sweet_potato_and_bean_patty",
    "potato_carrot_and_onion_patty",
    "romaine_lettuce_pea_and_tomato_patty",
    "sweet_potato_spinach_and_mushroom_patty",
    "taro_bean_and_bell_pepper_patty",
    "zucchini_green_pea_and_onion_patty",
]

CSV_COLUMNS = [
    "model",
    "order",
    "success_rate",
    "time_avg",
    "time_var",
    "mean_f1_agent_0",
    "mean_similarity_agent_0",
    "mean_redundancy_agent_0",
    "std_f1_agent_0",
    "std_similarity_agent_0",
    "std_redundancy_agent_0",
    "mean_f1_agent_1",
    "mean_similarity_agent_1",
    "mean_redundancy_agent_1",
    "std_f1_agent_1",
    "std_similarity_agent_1",
    "std_redundancy_agent_1",
    "initiate_collaboration",
    "respond_collaboration",
    "overall_collaboration",
]


def parse_list_argument(value):
    if not value:
        return []
    return [item.strip() for item in value.replace(",", " ").split() if item.strip()]


def read_existing_csv(excel_path):
    if os.path.exists(excel_path):
        return pd.read_csv(excel_path)
    return pd.DataFrame(columns=CSV_COLUMNS)


def main(variant):
    order = variant["order"]
    eval_result_dir = os.path.join(variant["eval_result_dir"], variant["model"])
    eval_file = os.path.join(eval_result_dir, order, "evaluation_result.json")

    if not os.path.exists(eval_file):
        print(f"Error: File {eval_file} not found.")
        return

    with open(eval_file, "r") as file:
        data = json.load(file)

    if order not in data:
        print(f"Error: Key '{order}' not found in evaluation_result.json.")
        return

    order_data = data[order]
    average = order_data.get("average", {})
    task_metrics = order_data.get("task_metrics", {})
    statistic = order_data.get("statistic", {})
    similarity = average["similarity_and_redundancy"]

    initiate_collaboration = statistic["initiate_collaboration"]
    respond_collaboration = statistic["respond_collaboration"]

    new_row = pd.DataFrame(
        [
            {
                "model": variant["model"],
                "order": order,
                "success_rate": task_metrics["success_rate"],
                "time_avg": task_metrics["time_avg"],
                "time_var": task_metrics["time_var"],
                "mean_f1_agent_0": similarity["agent_0"]["mean_f1"],
                "mean_similarity_agent_0": similarity["agent_0"]["mean_similarity"],
                "mean_redundancy_agent_0": similarity["agent_0"]["mean_redundancy"],
                "std_f1_agent_0": similarity["agent_0"]["std_f1"],
                "std_similarity_agent_0": similarity["agent_0"]["std_similarity"],
                "std_redundancy_agent_0": similarity["agent_0"]["std_redundancy"],
                "mean_f1_agent_1": similarity["agent_1"]["mean_f1"],
                "mean_similarity_agent_1": similarity["agent_1"]["mean_similarity"],
                "mean_redundancy_agent_1": similarity["agent_1"]["mean_redundancy"],
                "std_f1_agent_1": similarity["agent_1"]["std_f1"],
                "std_similarity_agent_1": similarity["agent_1"]["std_similarity"],
                "std_redundancy_agent_1": similarity["agent_1"]["std_redundancy"],
                "initiate_collaboration": initiate_collaboration,
                "respond_collaboration": respond_collaboration,
                "overall_collaboration": (
                    initiate_collaboration + respond_collaboration
                )
                / 2,
            }
        ]
    )

    excel_path = os.path.join(variant["eval_result_dir"], variant["output"])
    df = read_existing_csv(excel_path)
    if not df.empty:
        df = df[~((df["model"] == variant["model"]) & (df["order"] == order))]
    df = pd.concat([df, new_row], ignore_index=True)

    os.makedirs(variant["eval_result_dir"], exist_ok=True)
    df.to_csv(excel_path, index=False)
    print(f"Data for order '{order}' saved to {excel_path}.")


if __name__ == "__main__":
    parser = ArgumentParser(description="Process evaluation results into CSV.")
    parser.add_argument("--model", type=str, default="gpt-4o", help="Model name")
    parser.add_argument(
        "--models", type=str, default=None, help="Comma or space separated model names"
    )
    parser.add_argument(
        "--order",
        type=str,
        default="AUTO",
        help="Task name. AUTO means all built-in tasks.",
    )
    parser.add_argument(
        "--orders", type=str, default=None, help="Comma or space separated task names"
    )
    parser.add_argument(
        "--eval_result_dir",
        type=str,
        default="eval_result",
        help="Directory containing evaluation results",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="statistics_data.csv",
        help="Output CSV filename under eval_result_dir",
    )
    args = parser.parse_args()
    variant = vars(args)

    start_time = time.time()
    model_list = parse_list_argument(variant.get("models")) or (
        DEFAULT_MODELS if variant["model"] == "AUTO" else [variant["model"]]
    )
    order_list = parse_list_argument(variant.get("orders")) or (
        DEFAULT_ORDERS if variant["order"] == "AUTO" else [variant["order"]]
    )

    for model in model_list:
        for order in order_list:
            variant["model"] = model
            variant["order"] = order
            main(variant)
    end_time = time.time()
    print("\n======= Finished all =======\n")
    print(f"Cost time: {end_time - start_time:.3f}s\n")
