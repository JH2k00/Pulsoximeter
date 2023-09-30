class CircularBuffer:
    """
    A CircularBuffer which holds its values in a FIFO format. After the buffer is filled up completly
    the oldest element gets removed for every new appending.
    """

    # TODO According to Micropython Stype Guides I shouldnt append items a list since this can avoke excesive
    #  ram usage and has a garbage collector call as consequence (which can take several milliseconds)

    def __init__(self, size: int):
        if size < 1: raise ValueError('Negative dimensions are not allowed')
        self.__buff = [0 for _ in range(size)]
        # index points to the next position where a new element will be inserted (counting from 0 to size -1)
        # self.__size = size
        # self.__index = size - 1

    def append(self, element: float, *args, **kwargs):
        """
        Append an element to the circular buffer and deques the last element of the buffer
        Parameters
        ----------
        element : new element which should be inserter. element has to be a single digit and must'nt be a list.
        """
        self.__buff.pop(0)
        self.__buff.append(element)

        # self.__index -= 1
        # self.__index = self.__index % self.__size

    def __repr__(self):
        return repr(self.__buff)  # + ', Index = {}, Size {}'.format(self.__index, len(self.__buff))

    def get_buffer(self):
        return self.__buff


class SensorBuffer():
    """
        An Implementation of a Circular Buffer specific for storing the raw readings from the MAX30102 sensor.
        TODO Maybe an even more generic multidimensional implementation might be better?
    """

    def __init__(self, size: int):
        self.__red_buffer = CircularBuffer(size)
        self.__ir_buffer = CircularBuffer(size)

    def append(self, red=0, ir=0, *args, **kwargs):
        """
        Append the given parameters to the CircularBuffer holding the sensor readings

        Parameters
        ----------
        red : raw read readings
        ir : raw ir readings
        millis : raw millis readings
        """
        self.__red_buffer.append(red)
        self.__ir_buffer.append(ir)

    def __repr__(self):
        return 'Red: ' + repr(self.__red_buffer) + '\n' + \
               'IR: ' + repr(self.__ir_buffer)

    def get_red(self):
        """

        Returns
        -------

        """
        return self.__red_buffer.get_buffer()

    def get_ir(self):
        """

        Returns
        -------

        """
        return self.__ir_buffer.get_buffer()


def test_circular_buffer():
    buff = CircularBuffer(10)
    print(buff)

    for i in range(16):
        buff.append(i)
        print(buff)


if __name__ == '__main__':
    test_circular_buffer()
