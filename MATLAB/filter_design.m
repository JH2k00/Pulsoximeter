fs = 50; % MAX30102's sampling rate is 50Hz
f = [0, 5/60, 30/60, 200/60, 225/60, fs/2]; % Non-normalized frequencies for filter design
f_norm = f./(fs/2); % Normalized frequencies
values = [0 0 1 1 0 0]; % Values for the corresponding frequencies
coeffs = firpm(299,f_norm,values);

figure;
[h,w] = freqz(coeffs,1,512);
plot(f_norm,values,w/pi,abs(h))
legend('Ideal','firpm Design')
xlabel('Radian Frequency (\omega/\pi)') 
ylabel('Magnitude')

figure;

plot(w/pi,angle(h)*180/pi)
legend('firpm Design')
xlabel('Radian Frequency (\omega/\pi)') 
ylabel('Phase (degrees)')