from typing import OrderedDict
from sklearn import manifold, mixture, metrics
from ltsa import LocalTangentSpaceAlignment as LTSA
import numpy as np

def unpickle(file):
    """
    From http://www.cs.toronto.edu/~kriz/cifar.html
    """
    import pickle
    with open(file, 'rb') as fo:
        dict = pickle.load(fo, encoding='bytes')
    return dict

class ManifoldHelper:

    def __init__(
        self, 
        n_neighbors=[10], 
        dimensions=[2], 
        methods=['ISOMAP'],
        sklearn_LTSA=False,
        eigen_solver='auto',
        gmm_n_init=5
    ):
        
        self.n_neighbors = n_neighbors
        self.dimensions = dimensions
        self.methods = methods
        self.sklearn_LTSA = sklearn_LTSA
        self.eigen_solver = eigen_solver
        self.gmm_n_init = gmm_n_init

    def fit_transform(self, X, method, n_neighbors, d_dimension) -> np.ndarray:
        """fit_transform
            Fit and transform X with manifold method and returns
            X_transformed with d_dimensions columns.
        """
        manifold_method = self._get_manifold_method(method, n_neighbors, d_dimension)
        return manifold_method.fit_transform(X)

    def evaluate_gmm_ari(self, X, Y, n_components) -> float:
        """gmm_ari
            Generates Gaussian Mixture Model with X
            and evaluate predicted results with Y.
        """
        gmm_predict = self._gmm_predict(X, n_components)
        return self._eval_ari(gmm_predict, Y)

    def evaluate_all(self, X, Y, n_components) -> OrderedDict:
        ari_results = OrderedDict()
        for m in self.methods:
            ari_results[m] = np.empty((len(self.dimensions), len(self.n_neighbors)))
        
        for i in range(len(self.dimensions)):
            d = self.dimensions[i]
            print(f'\n{d}_dimension:', end='')

            for j in range(len(self.n_neighbors)):
                n = self.n_neighbors[j]
                print(f'\n   {n}_neighbors:', end='')

                for m in self.methods:
                    try:
                        Xd = self.fit_transform(X, m, n, d)
                        ari_results[m][i, j] = self.evaluate_gmm_ari(Xd, Y, n_components)
                    except:
                        # LTSA may fail
                        ari_results[m][i, j] = 0.0
                    print(f' {ari_results[m][i, j]:.2f} ', end='')
        return ari_results
                    

    def _get_manifold_method(
        self, 
        method_name, 
        n_neighbors,
        d_dimension
    ) -> manifold:
        """__get_manifold_method
            Returns sklearn.manifold object corresponding to method_name.
        """
        if method_name == 'ISOMAP':
            return manifold.Isomap(
                n_neighbors=n_neighbors, 
                n_components=d_dimension,
            )
        elif method_name == 'LLE':
            return manifold.LocallyLinearEmbedding(
                n_neighbors=n_neighbors,
                n_components=d_dimension,
                random_state=42
            )
        elif method_name == 'SE':
            return manifold.SpectralEmbedding(
                n_neighbors=n_neighbors,
                n_components=d_dimension,
                random_state=42
            )
        elif method_name == 'LTSA':
            if self.sklearn_LTSA:
                return manifold.LocallyLinearEmbedding(
                    n_neighbors=n_neighbors,
                    n_components=d_dimension,
                    method='ltsa',
                    eigen_solver=self.eigen_solver,
                    random_state=42
                )
            else:
                return LTSA(n_neighbors=n_neighbors, n_components=d_dimension)
    
    def _gmm_predict(self, X, n_components) -> list:
        """__gmm_predict
            Creates a Gaussian Mixture Model and predicts labels.
        """
        gmm = mixture.GaussianMixture(n_components=n_components, n_init=self.gmm_n_init, random_state=42)
        return gmm.fit(X).predict(X)

    def _eval_ari(self, X, Y) -> float:
        """__eval_ari
            Evaluates X and Y with Adjusted Rand Index (ARI)
        """
        return metrics.adjusted_rand_score(X, Y)