# -*- coding: utf-8 -*-
"""Dar kapsamli, AST-kisitlamali SymPy dogrulamasi.
Bu katman modelin tum ispatlarini dogrulamaz; acik ifadeleri hesaplar.
"""
import ast
import re
import sympy as sp

x, y, t = sp.symbols('x y t')
SYMBOLS = {'x': x, 'y': y, 't': t, 'pi': sp.pi, 'e': sp.E, 'E': sp.E}
FUNCS = {'sqrt': sp.sqrt, 'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
         'exp': sp.exp, 'log': sp.log, 'ln': sp.log, 'abs': sp.Abs}


def _read(node, depth=0):
    if depth > 25:
        raise ValueError('Matematik ifadesi cok karmasik.')
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        if abs(node.value) > 10**10:
            raise ValueError('Sayi siniri asildi.')
        return sp.Rational(str(node.value))
    if isinstance(node, ast.Name) and node.id in SYMBOLS:
        return SYMBOLS[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        z = _read(node.operand, depth+1)
        return z if isinstance(node.op, ast.UAdd) else -z
    if isinstance(node, ast.BinOp):
        a, b = _read(node.left, depth+1), _read(node.right, depth+1)
        if isinstance(node.op, ast.Add): return a+b
        if isinstance(node.op, ast.Sub): return a-b
        if isinstance(node.op, ast.Mult): return a*b
        if isinstance(node.op, ast.Div): return a/b
        if isinstance(node.op, ast.Pow):
            if b.is_number is not True or b.is_real is not True or abs(float(b)) > 20:
                raise ValueError('Us cok buyuk veya degisken.')
            return a**b
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in FUNCS and len(node.args) == 1 and not node.keywords):
        return FUNCS[node.func.id](_read(node.args[0], depth+1))
    raise ValueError('Desteklenmeyen veya guvensiz ifade.')


def ifade(metin):
    s = str(metin or '').strip().replace('π','pi').replace('²','^2').replace('³','^3')
    s = s.replace('−','-').replace('×','*').replace('^','**')
    # Yaygin lise yazimlari: 2x, 3pi, sin x, 2(x+1)
    s = re.sub(r'(?<=\d)(?=[xyt])', '*', s)
    s = re.sub(r'(?<=\d)(?=pi\b)', '*', s)
    s = re.sub(r'\b(sin|cos|tan|sqrt|exp)\s+([xyt])\b', r'\1(\2)', s)
    s = re.sub(r'(?<=\d)(?=\()', '*', s)
    if not s or len(s) > 180:
        raise ValueError('Ifade bos veya cok uzun.')
    # Acik carpma kullan: 2*x (2x model tarafinda standartlastirilmali)
    if re.search(r'\b(?:import|exec|eval|lambda)\b', s, re.I):
        raise ValueError('Gecersiz ifade.')
    return _read(ast.parse(s, mode='eval').body)


def dogrula(veri):
    """Yapilandirilmis bir soruda dogrulanabilen islemler icin sonuc dondurur."""
    tur = str(veri.get('sympy_task') or 'none').lower()
    es = str(veri.get('expression') or '').strip()
    if not es or tur in ('none','other',''):
        return None
    deg = SYMBOLS.get(str(veri.get('variable') or 'x'), x)
    if tur == 'solve':
        if '=' in es:
            left, right = es.split('=', 1)
            nesne = ifade(left)-ifade(right)
        else:
            nesne = ifade(es)
        result = sp.solve(nesne, deg)
        return {'islem': 'Denklemin kokleri', 'sonuc': ', '.join(map(str,result)) or 'Kok bulunamadi'}
    f = ifade(es)
    if tur == 'evaluate':
        at = ifade(veri.get('at'))
        result = sp.simplify(f.subs(deg, at))
        return {'islem': f'{deg}={at} icin deger', 'sonuc': str(result)}
    if tur == 'derivative':
        return {'islem':'Turev', 'sonuc':str(sp.diff(f,deg))}
    if tur == 'factor':
        return {'islem':'Carpanlara ayirma','sonuc':str(sp.factor(f))}
    if tur == 'simplify':
        return {'islem':'Sadeleştirme','sonuc':str(sp.simplify(f))}
    if tur in ('integral', 'volume'):
        aa = veri.get('lower_bound')
        bb = veri.get('upper_bound')
        if aa in (None,'') or bb in (None,''):
            if tur == 'volume': return None
            result = sp.integrate(f,deg)
        else:
            a,b = ifade(aa),ifade(bb)
            if a.is_number is not True or b.is_number is not True:
                raise ValueError('Sinirlar sayi olmali.')
            integrand = sp.pi*f**2 if tur == 'volume' else f
            result = sp.integrate(integrand,(deg,a,b))
        if result.has(sp.Integral): return None
        return {'islem':'Donel cisim hacmi' if tur == 'volume' else 'Integral',
                'sonuc': str(sp.simplify(result))}
    return None


def stl_uygun_mu(veri):
    """STL yalniz x ekseni etrafinda, tek fonksiyonlu ve iki sinirli disk icin."""
    if str(veri.get('question_type','')).lower() != 'solid_of_revolution': return False
    if str(veri.get('rotation_axis','x')).strip().lower() not in ('x','x-axis','x_ekseni'):
        return False
    if str(veri.get('inner_expression') or '').strip() not in ('','0','0.0'):
        return False
    for key in ('solid_function','lower_bound','upper_bound'):
        if not str(veri.get(key) or '').strip(): return False
    try:
        f = ifade(veri['solid_function'])
        a,b = ifade(veri['lower_bound']),ifade(veri['upper_bound'])
        return f.free_symbols <= {x} and a.is_number and b.is_number and bool(b>a)
    except (ValueError, SyntaxError, TypeError, AttributeError):
        return False
