#!/usr/bin/env python2.6
# coding: utf-8

def print_table( f ):

    k = 0
    for i in f:
        print('%02x' % i, end=' ')
        k += 1
        if k % 16 == 0:
            print()

    print()

class Field( object ):

    def __init__( self, order, characteristic ):
        self.order = order

        self.power = [ 0 ] * self.order
        self.log = [ 0 ] * self.order

        # x^8 + x^4 + x^3 + x^2 + 1
        self.prime = 0b100011101
        # generator
        self.primitive = 2

        # AES use 0x1b as prime polynomial:
        # https://en.wikipedia.org/wiki/Finite_field_arithmetic#Primitive_polynomials
        # https://en.wikipedia.org/wiki/Finite_field_arithmetic#Rijndael's_(AES)_finite_field
        self.prime = 0b100011011
        self.primitive = 3

        self.make_field()

    def make_field( self ):

        n = 1

        for i in range( 0, 256 ):

            self.power[ i ] = n

            assert self.log[ n ] == 0
            self.log[ n ] = i

            #  n ⊗= self.primitive % prime
            mul = 0
            p = self.primitive
            tmp = n
            while p > 0:
                if p & 1 == 1:
                    mul ^= tmp
                    if mul >= self.order:
                        mul = mul ^ self.prime
                tmp <<= 1
                p >>= 1
            n = mul

            #  if n >= self.order:
            #      n = n ^ self.prime

        # fix or log( 1 ) -> 255
        self.log[ 1 ] = 0

        assert len( set(self.power) ) == 255
        assert len( set(self.log) ) == 255

        print_table( self.power )
        print_table( self.log )

f = Field( 256, 2 )

def f_pow( x, power ):
    assert x < f.order

    l = f.log
    lg = l[ x ] * power
    lg = lg % f.order

    return f.power[ lg ]

def f_log(base, x):
    l = f.log

    lg_b = l[base]
    lg_x = l[x]

    assert lg_x % lg_b == 0

    return lg_x / lg_b

def f_mul( a, b ):
    assert a < f.order
    assert b < f.order

    if a * b == 0:
        return 0

    l = f.log
    lg_a = l[ a ]
    lg_b = l[ b ]

    lg = (lg_a + lg_b) % (f.order-1)

    return f.power[ lg ]

def f_div( a, b ):
    assert a < f.order
    assert b < f.order

    l = f.log
    lg_a = l[ a ]
    lg_b = l[ b ]

    lg = (lg_a - lg_b) % (f.order-1)

    return f.power[ lg ]

def f_add( a, b ):
    assert a < f.order
    assert b < f.order

    c = a ^ b

    return c

def enc( messages, nr_rep ):
    n = len( messages )

    codes = []

    for i in range( nr_rep ):

        code = enc_line( messages, i )

        codes.append( code )

    return codes

def enc_line( messages, power ):
    code = 0
    n = len( messages )
    for i_mes in range( n ):
        coefficient = f_pow( i_mes+1, power )
        r = f_mul( coefficient, messages[ i_mes ] )
        print(coefficient, messages[ i_mes ], r, '        ', end=' ')
        code = f_add( code, r )

    print()
    print('enc_line mes, power=', messages, power, code)
    return code

def determinant( matrix ):

    if len( matrix ) == 1:
        return matrix[ 0 ][ 0 ]

    rst = 0

    for j in range( len(matrix[ 0 ]) ):

        sub = []

        for line in matrix[ 1: ]:
            l = line[:]
            l.pop( j )
            sub.append( l )
        sub = f_mul( matrix[0][j], determinant( sub ) )
        rst = f_add( rst, sub )

    return rst

def dec( messages, codes ):

    assert len( codes ) <= 2

    mes = messages[:]

    # make None 0 thus skips that element
    mes = [ (x or 0) for x in mes ]

    rst = messages[:]

    if codes[ 0 ] is None:
        if codes[ 1 ] is None:
            return messages
        else:
            assert len( [ x for x in messages if x is None ] ) == 1
            i_lost = messages.index( None )
            ss = enc_line( mes, 1 )
            code = f_add( codes[ 1 ], ss )
            coefficient = f_pow( i_lost + 1, 1 )
            print('coefficient', coefficient)

            rst[ i_lost ] = f_div( code, coefficient )
    else:
        if codes[ 1 ] is None:
            pass
        else:
            # 2 lost 2 codes
            lost_indexes = [ i for i in range(len(messages))
                        if messages[ i ] is None ]
            assert len( lost_indexes ) == 2

            codes = [ f_add(codes[ i ], enc_line( mes, i ))
                      for i in range( 2 ) ]

            print('codes', codes)
            coeff = [ [ f_pow( lost_indexes[ i ]+1, power )
                        for i in (0, 1) ]
                      for power in (0, 1) ]

            print('coeff:', coeff)

            divider = determinant( coeff )
            print('divider', divider)
            for i in range(len(lost_indexes)):
                idx = lost_indexes[ i ]
                ff = [ line[:] for line in coeff ]
                for j in range( 2 ):
                    ff[ j ][ i ] = codes[ j ]

                print(ff)

                f_det = determinant( ff )
                print(f_det)
                rst[ idx ] = f_div( f_det, divider )


    return rst

def main():

    # print f_mul( 1, 0 )
    # print f_mul( 0, 1 )

    mes = [ 8, 234, 83 ]
    code = enc( mes, 2 )
    print('got::', code)

    lost = mes[:]
    lost[ 1 ] = None
    lost[ 2 ] = None
    lost_code = code
    recovered = dec( lost, lost_code )
    print(lost, lost_code, recovered)



    # print determinant( [
    #         [ 1, 2, 3 ],
    #         [ 3, 4, 5 ],
    #         [ 2, 3, 2 ],
    # ] )

def cmd_g_mul():
    import sys
    a, b = sys.argv[ 1:3 ]
    a = int( a, 16 )
    b = int( b, 16 )
    print('%02x' % f_mul( a, b ))

if __name__ == "__main__":
    main()

    # cmd_g_mul()
