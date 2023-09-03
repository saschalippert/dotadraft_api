FROM archlinux:latest

RUN echo 'root:root' | chpasswd

RUN echo 'en_US.UTF-8 UTF-8' > /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8
RUN ln -sf /usr/share/zoneinfo/Europe/Berlin /etc/localtime

RUN pacman -Syyu --noconfirm

RUN pacman -S --noconfirm sudo git base-devel nano net-tools curl python python-pip tor

RUN pip3 install zmq aiohttp numpy pytweening pyyaml python-dateutil jsonpickle coloredlogs

COPY torrc /etc/tor/torrc

EXPOSE 9050

CMD [ "/bin/tor" ]