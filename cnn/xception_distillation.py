from keras.models import Sequential
from keras.layers import Convolution2D, MaxPooling2D
from keras.layers import Activation, Dropout, Flatten, Dense, Add
from keras.preprocessing.image import ImageDataGenerator
from xception import Xception

# parameters
import argparse
parser = argparse.ArgumentParser(description='xception doctor')
parser.add_argument('--batch-size', type=int, default=32,
                    help='batch size')
parser.add_argument('--epoch', type=int, default=10,
                    help='epoch')
parser.add_argument('--rescale', type=int, default=128,
                    help='rescale image size')
parser.add_argument('--part', type=str, default='brain',
                    help='body part')
args = parser.parse_args()

print('####',args.part)

### setup dataset
data_dir = '../data/' + args.part 
target_size = (args.rescale, args.rescale)

train_datagen = ImageDataGenerator(
    rescale=1.0 / 255,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True)

test_datagen = ImageDataGenerator(rescale=1.0 / 255)

train_generator = train_datagen.flow_from_directory(
    data_dir + '/train',
    target_size=target_size,
    batch_size=args.batch_size,
    class_mode='categorical')

validation_generator = test_datagen.flow_from_directory(
    data_dir + '/validation',
    target_size=target_size,
    batch_size=args.batch_size,
    class_mode='categorical')

class EducateGenerator(object):
    def __init__(self, train_generator):
        self.train_generator = train_generator
        self.validation_generator = validation_generator
    def __next__(self):
        x_train, y_train = self.train_generator.next()
        return ( [x_train,x_train], y_train )
    def next(self):
        return self.__next__()

# .next() -> ([x_train,x_train],y_train)
educate_generator = EducateGenerator(
    train_generator)
    #, validation_generator)


### build teacher model
n_labels = train_generator.num_class
print('{} labels'.format(n_labels), train_generator.class_indices)

teacher = Xception(
    weights=None,
    classes=n_labels)

teacher.summary()

teacher.compile(loss='categorical_crossentropy',
               optimizer='adam',
               metrics=['accuracy'])
teacher.load_weights(
    'models/xception.rescale=128.eyes.weghit.h5')


### build student model
student = Sequential()
student.add(Convolution2D(32, 3, 3, input_shape=(128, 128, 3)))
student.add(Activation('relu'))
student.add(MaxPooling2D(pool_size=(2, 2)))

student.add(Convolution2D(64, 3, 3))
student.add(Activation('relu'))
student.add(MaxPooling2D(pool_size=(2, 2)))

student.add(Flatten())
student.add(Dense(64))
student.add(Activation('relu'))
student.add(Dropout(0.5))
student.add(Dense(2))
student.add(Activation('softmax'))

student.summary()

student.compile(loss='categorical_crossentropy',
               optimizer='adam',
               metrics=['accuracy'])


### teacher educat student
from keras.layers import Activation, Dence, Add
negativeActivation = lambda x: -x

negativeRight = Activation(negativeActivation)(student.output) 
diff = Add()([teacher.output,negativeRight])

model = Model(inputs=[teacher.input, student.input], outputs=[diff])
model.compile(loss='mean_squared_error', optimizer='Adam', metrics=['acc'])

model.summary(line_length=150)
#model.fit([X_train, X_train], [Y_train], batch_size=128, nb_epoch=5)
history = model.fit_generator(
    educate_generator,
    steps_per_epoch=200,#train_generator.n//batch_size,
    epochs=5)
    #validation_data=validation_generator,
    #validation_steps=20)

print(student.evaluate(
    train_generator, validatin_generator))

### save model weights 
import os
result_dir = './models/'
student.save(os.path.join(result_dir, 
    'xception_student.rescale={}.{}.model.h5'.format(args.rescale, args.part)))
student.save_weights(os.path.join(result_dir, 
    'xception_student.rescale={}.{}.weghit.h5'.format(args.rescale, args.part)))
