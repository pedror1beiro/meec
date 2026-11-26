function a = thorp(f_kHz)
%THORP Coeficiente de absorcao do som na agua do mar [dB/km] (Thorp).
%   a = thorp(f_kHz), com f em kHz. Aproximacao adequada ~0.1-100 kHz.
f2 = f_kHz.^2;
a  = 0.11*f2./(1+f2) + 44*f2./(4100+f2) + 2.75e-4*f2 + 0.003;
end
