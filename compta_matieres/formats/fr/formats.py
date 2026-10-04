# Formats français propres à l'application (surchargent ceux de Django).
# Montants : point comme séparateur de milliers, virgule pour les décimales
# → 150.000 ou 150.000,50. Les autres formats (dates…) restent ceux de Django.
DECIMAL_SEPARATOR = ','
THOUSAND_SEPARATOR = '.'
NUMBER_GROUPING = 3
