import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
import tensorflow.keras.models as models
import tensorflow.keras.layers as layers
import tensorflow.keras.optimizers as optimizers
from tensorflow.keras.regularizers import l2
# import keras_tuner


class convNet:
    def __init__(self, inputShape, convSize, convDepth):
        #@Param inputShape : the shape of thew observation -> transformed board state
        #@param convSize : the size of the filter (will be the outputy size)
        #@param convDepth : Number of Convolution layers in the model
        self.inputShape = inputShape
        self.buildConvNet(convSize, convDepth)
        
    def buildConvNet(self, convSize, convDepth, hp=None):
        #@param convSize : the size of the filter (will be the outputy size)
        #@param convDepth : Number of Convolution layers in the model
        #@param hp : Hyperparameters for the model
        # Define input layers
        board_3d = layers.Input(shape=self.inputShape)
        boardSize = 8*8
        
        # This creates the hidden layers in the convNet
        x = board_3d
        for _ in range(convDepth):
            x = layers.Conv2D(filters=convSize, kernel_size=3, padding='same', activation='relu', data_format="channels_last", kernel_regularizer=l2(0.01), bias_regularizer=l2(0.01))(x)
        # The curr size of x is (?, convSize, 8, 8)
        x = layers.Flatten()(x)
        for _ in range(3):
            x = layers.Dense(boardSize*6, "relu",kernel_regularizer=l2(0.01), bias_regularizer=l2(0.01))(x) # An array of size convSize * boardSize
        x = layers.Dropout(rate=0.25)(x)
        # x = layers.Reshape((76, 8, 8))(x)
        # dot product of x
        x = layers.Dense(1)(x)
        
        
        self.model = models.Model(inputs=board_3d, outputs=x)
        learning_rate = hp.Float("lr", min_value=1e-4, max_value=1e-2, sampling="log") if hp is not None else 5e-4
        self.model.compile(
            optimizer=optimizers.AdamW(learning_rate=learning_rate),
            loss="mean_squared_error",
            metrics=["accuracy"],
        )
        # self.model.compile(optimizer = optimizers.Adam(5e-4), loss='mean_squared_error')
    
    def fit(self, train_x, train_y, epochs=100):
        assert train_x.shape[0] == train_y.shape[0]
        self.model.fit(train_x, train_y, epochs=epochs)
        
    def forward(self, board):
        #@param board : same dims as inputShape -> representatio of board state
        print(board.shape)
        return self.model.predict(board)
    

# net = convNet((8, 8, 14), 76, 3)
# print(net.model.summary())

# train_x = np.random.uniform(0, 1, size=(100, 8, 8, 14))
# train_y = np.random.uniform(0, 1, size=(100, 76*8*8))
# print("x: " + str(train_x.shape))
# print("Y: " + str(train_y.shape))
# net.fit(train_x, train_y, epochs=5)
# print(net.forward(np.random.uniform(1, 2, size=(8, 8, 14))))
    
if __name__ == '__main__':
    net = convNet((12,8,8), 32, 2)
    model = net.model
    model.compile(optimizer=optimizers.Adam(), loss='binary_crossentropy')
    model.summary()
    # utils.plot_model(model, to_file='model.png', show_shapes=True)
    