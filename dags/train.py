"""
Training the model
"""
import json
import pandas as pd
import numpy as np

pd.options.display.max_columns = 100
pd.options.display.max_rows = 60
pd.options.display.max_colwidth = 100
pd.options.display.precision = 10
pd.options.display.width = 160

from sklearn.model_selection import train_test_split, GridSearchCV, KFold
from sklearn.metrics import precision_score, recall_score
from sklearn.ensemble import RandomForestClassifier
from features import FeatureProcessor, FeatureSets

from db_utils import Database

# import mlflow

# remote_server_uri = "http://localhost:8088"
# mlflow.set_tracking_uri(remote_server_uri)

# # set experiment
# mlflow.set_experiment("experiment_01")

# mlflow.sklearn.autolog()

# load data


def load_data(n_samples):
    db = Database()
    query = f"""
select * from dpe_training
order by created_at desc
limit {n_samples}
"""
    df = pd.read_sql(query, con=db.engine)
    db.close()
    # dump payload into new dataframe
    df["payload"] = df["payload"].apply(lambda d: json.loads(d))

    data = pd.DataFrame(list(df.payload.values))
    data.drop(columns="n_dpe", inplace=True)
    data = data.astype(int)
    return data


class NotEnoughSamples(ValueError):
    pass


class TrainDPE:
    param_grid = {
        "n_estimators": [50, 100],  # Number of trees
        "max_depth": [2, 4],  # Maximum depth of the trees
        "min_samples_leaf": [2, 5],  # Maximum depth of the trees
    }
    n_splits = 3
    test_size = 0.3
    minimum_training_samples = 100

    def __init__(self, data, target="etiquette_dpe"):
        # drop samples with no target
        data = data[data[target] >= 0].copy()
        data.reset_index(inplace=True, drop=True)
        if data.shape[0] < TrainDPE.minimum_training_samples:
            raise NotEnoughSamples(
                "data has {data.shape[0]} samples, which is not enough to train a model. min required {TrainDPE.minimum_training_samples}"
            )

        self.data = data
        self.model = RandomForestClassifier()
        self.target = target
        self.params = {}
        self.train_score = 0.0

        self.precision_score = 0.0
        self.recall_score =  0.0
        self.probabilities =  [0.0, 0.0]


    def main(self):
        # shuffle
        # data = data.sample(frac=1, random_state=808).reset_index(drop=True)
        # drop n_dpe, targets

        X = self.data[FeatureSets.train_columns].copy()  # Features
        y = self.data[self.target].copy()  # Target variable

        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=TrainDPE.test_size, random_state=808
        )

        # Setup GridSearchCV with k-fold cross-validation
        cv = KFold(n_splits=TrainDPE.n_splits, random_state=42, shuffle=True)

        grid_search = GridSearchCV(
            estimator=self.model, param_grid=TrainDPE.param_grid, cv=cv, scoring="accuracy"
        )

        # Fit the model
        grid_search.fit(X_train, y_train)

        self.model = grid_search.best_estimator_
        self.params = grid_search.best_params_
        self.train_score = grid_search.best_score_

        yhat = grid_search.predict(X_test)
        self.precision_score = precision_score(y_test, yhat, average="weighted")
        self.recall_score = recall_score(y_test, yhat, average="weighted")
        self.probabilities = np.max(grid_search.predict_proba(X_test), axis=1)

    def report(self):
        # Best parameters and best score
        print("--"*20, "Best model")
        print(f"\tparameters: {self.params}")
        print(f"\tcross-validation score: {self.train_score}")
        print(f"\tmodel: {self.model}")
        print("--"*20, "performance")
        print(f"\tprecision_score: {np.round(self.precision_score, 2)}")
        print(f"\trecall_score: {np.round(self.recall_score, 2)}")
        print(f"\tmedian(probabilities): {np.round(np.median(self.probabilities), 2)}")
        print(f"\tstd(probabilities): {np.round(np.std(self.probabilities), 2)}")


if __name__ == "__main__":
    data = load_data(n_samples = 3000)
    train = TrainDPE(data)
    train.main()
    train.report()

