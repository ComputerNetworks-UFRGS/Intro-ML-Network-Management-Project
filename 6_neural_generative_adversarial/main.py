# Importando bibliotecas necessárias

# Biblioteca para listagem de arquivos

# Atenção, esse algoritmo demora algumas horas para treinar

from glob import glob

# Biblioteca para abrir imagens
import cv2.cv2

# Bibliote numérica
import numpy

# Convolução bidimensional
from keras.layers import Conv2D

# Activations do keras: [relu - softmax - LeakyReLU - prelu - elu - thresholdedrelu]
from keras.layers import Activation, MaxPooling2D

# Dense é a rede "tradicional", neurônios simples
from keras.layers import Dense

# Usado para achatar saídas ou entradas em rede neurais 2D->1D [[1.4, 1.1], [1.8, 3.1]] -> [1.4, 1.1, 1.8, 3.1]
from keras.layers import Flatten

# Layers para definir o formato da rede neural
from keras.layers import Input

# Camada capaz de redimensionar o formato sa saída de uma layer
from keras.layers import Reshape

# Camada de pooling médio reduz a dimensão
from keras.layers import AveragePooling2D

# Camada que amplia um imagem
from keras.layers import UpSampling2D

# Camada de preenchimento com zeros
from keras.layers import ZeroPadding2D

# Classe modelo para as rede neurais(Pode ser feito na mão caso achem melhor)
from keras.models import Sequential
from keras.models import Model

# Função de "atualização" dos pesos na rede neural("Perda"), é necessária para o treinamento
from keras.optimizers import Adam

# Criar barrinha de carregamento de imagens
from tensorflow.python.keras.optimizers import adam
from tqdm import tqdm

# Importando tensorflow
import tensorflow as tf


# Função responsável por criar o gerador imagens,
# que a partir do ruído aleatório(pontos de latência) irá criar a imagem fake
def funcao_criar_gerador_image():
    # Instância do model
    model = Sequential()

    # Camada de densa responsável por receber os ruídos
    # Cada camada é ativada com uma relu
    model.add(Dense(6 * 9 * 256, input_dim=200))

    # Camade de transformação, recebe 13824 saídas da camada densa
    # e devolve 256 imagens (6 x 9)
    model.add(Reshape((6, 9, 256)))

    # Camadas convolutivas, a partir daqui o padrão será:

    # Conv2D(Filtros, tamanho_filtros, Normalização)
    # UpSampling2D() <- Aumenta o tamanho da imagem
    # ZeronPadding2D <- Preenchimento
    # A ideia principal é aumentar de forma progressiva a saida até o tamanho máximo da imagem

    model.add(Conv2D(128, kernel_size=(3, 3), padding="same"))
    model.add(UpSampling2D())
    model.add(ZeroPadding2D(padding=((0, 1), (0, 1))))

    model.add(Conv2D(128, kernel_size=(3, 3), padding="same"))
    model.add(UpSampling2D())
    model.add(ZeroPadding2D(padding=((0, 1), (0, 1))))

    model.add(Conv2D(64, kernel_size=(3, 3), padding="same"))
    model.add(UpSampling2D())
    model.add(ZeroPadding2D(padding=(0, (1, 0))))

    model.add(Conv2D(32, kernel_size=(3, 3), padding="same"))
    model.add(UpSampling2D())

    model.add(Conv2D(32, kernel_size=(3, 3), padding="same"))
    model.add(UpSampling2D())

    model.add(Conv2D(16, kernel_size=(3, 3), padding="same"))

    model.add(Conv2D(3, kernel_size=(1, 1), padding="same"))
    model.add(Activation("tanh"))

    # Aqui eu ligo a entrada do modelo, ao modelo em si
    entrada_ruidos = Input(shape=(200,))
    saida_modelo = model(entrada_ruidos)

    return Model(entrada_ruidos, saida_modelo)


# Essa função é responsável por instânciar o discriminador de imagem
# Na prática ele funciona como um "reconhecedor de padrões na image"
# Esse modelo que irá "avaliar" o modelo de geração
# Ele não deve ser treinado, caso contrário ele irá aprender a produzir um único valor de saída
# mesmo com entradas diferentes

def funcao_criar_discriminador_imagem():

    model = Sequential()

    model.add(Conv2D(32, kernel_size=3, strides=2, input_shape=(200, 300, 3), padding="same"))
    model.add(MaxPooling2D())

    model.add(Conv2D(64, kernel_size=3, strides=2, padding="same"))
    model.add(MaxPooling2D())

    model.add(Conv2D(128, kernel_size=3, strides=2, padding="same"))
    model.add(MaxPooling2D())

    model.add(Conv2D(128, kernel_size=3, strides=1, padding="same"))

    model.add(Flatten())

    model.add(Dense(1, activation='sigmoid'))

    entrada_image = Input(shape=(200, 300, 3))
    validadecao_model = model(entrada_image)

    return Model(entrada_image, validadecao_model)

# Essa função serve para converter a imagem para um formato compatível com TensorFlow.
# Na prática ela abre a imagem, decodifica, converte para float e redimensiona a imagem.


def converte_image_formato_tensorflow(nome_arquivo):

    imagem_carregada = tf.io.read_file(nome_arquivo)
    imagem_carregada = tf.image.decode_png(imagem_carregada, channels=3)
    imagem_carregada = tf.image.convert_image_dtype(imagem_carregada, tf.float32)
    imagem_carregada = tf.image.resize(imagem_carregada, [200, 300]) / 255.0
    return imagem_carregada



# Aqui estou instânciando o discriminador de imagem
modelo_discriminador = funcao_criar_discriminador_imagem()

# Aqui estou instânciando o gerador de imagem
modelo_gerador = funcao_criar_gerador_image()

# Definição do otimizador. Nesse caso, foi escolhido o Adam (Gradiente estocástico) usado pelo Multilayer Perceptron
# Optimizer do keras:  [SGD, RMSprop, Adam, Adadelta, Adagrad, Adamax, Nadam, Ftrl]
# lr = Taxa de aprendizado. É um valor que multiplica o valor de ajuste do peso.
# Valores altos de lr podem dificultar o treinamento, valores muito baixos tornam a aprendizagem demorada.
# Momentum é uma forma de acelerar o treinamento.
# Momentum https://machinelearningmastery.com/gradient-descent-with-momentum-from-scratch/
opt = adam(lr=0.01)

# O modelo precisa ser compilado, para isso chamamos compile()
# Metrics é utilizado para avaliar seu modelo.
#Accuracy metrics: accuracy, binary_accuracy, categorical_accuracy, top_K_categorical_accuracy, etc..
#Probabilistic metrics: binary_crossentropy, categorical_crossentropy, sparse_categorical_crossentropy, poisson
#Regression metrics: mean_squared_error, root_mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
# compile(<optimizer>, <loss>, <metrics>)

modelo_discriminador.compile(loss='binary_crossentropy', optimizer=adam, metrics=['accuracy'])

# Aqui estou especificando que o discriminador não deve ser treinado
modelo_discriminador.trainable = False

z = Input(shape=(200,))
img = modelo_gerador(z)
valid = modelo_discriminador(img)

rede_gan = Model(z, valid)
rede_gan.compile(loss='binary_crossentropy', optimizer=optimizer)

dos = glob("drive/MyDrive/dataset/*")

image_list = []

for i in tqdm(dos):
    image_list.append(converte_image_formato_tensorflow(i))

X_train = numpy.asarray(image_list, dtype="int32")

ones = numpy.ones((30, 1))
zeros = numpy.zeros((30, 1))

epoch = 0
noise = numpy.random.normal(0, 1, (30, 200))
idx = numpy.random.randint(0, X_train.shape[0], 30)

while (1):

    epoch += 1

    imgs = X_train[idx]

    gen_imgs = modelo_gerador.predict(noise)
    d_loss_r = modelo_discriminador.train_on_batch(imgs, ones)
    d_loss_f = modelo_discriminador.train_on_batch(gen_imgs, zeros)
    d_loss = numpy.add(d_loss_r, d_loss_f) * 0.5

    g_loss = rede_gan.train_on_batch(noise, ones)

    if epoch % 100 == 0:
        rand_noise = numpy.random.normal(0, 1, (1, 200))
        pred = modelo_gerador.predict(rand_noise)
        confidence = modelo_discriminador.predict(pred)
        gen_img = (0.5 * pred[0] + 0.5) * 255

        print("%d D loss: %f, acc.: %.2f%% G loss: %f" % (epoch, d_loss[0], 100 * d_loss[1], g_loss / 10))
        cv2.imwrite('drive/MyDrive/imagens/image_saida' + str(epoch) + '.png', gen_img)

    if epoch == 1000000:
        break
