"""robo controller."""
import numpy as np
import math
import matplotlib.pyplot as plt
import time

# Parameters
k = 0.1  # look forward gain
Lfc = 0.01  # [m] look-ahead distance
Kp = 0.01  # speed proportional gain
dt = 0.1  # [s] time tick
WB = 0.065  # [m] wheel base of vehicle




class State:

    def __init__(self, x=0.0, y=0.0, yaw=0.0, v=0.0):
        self.x = x
        self.y = y
        self.yaw = yaw
        self.v = v
        self.rear_x = self.x - ((WB / 2) * math.cos(self.yaw))
        self.rear_y = self.y - ((WB / 2) * math.sin(self.yaw))

    def update(self, a, delta):
        # self.x += self.v * math.cos(self.yaw) * dt
        # self.y += self.v * math.sin(self.yaw) * dt
        # self.yaw += self.v / WB * math.tan(delta) * dt
        # self.v += a * dt
        self.rear_x = self.x - ((WB / 2) * math.cos(self.yaw))
        self.rear_y = self.y - ((WB / 2) * math.sin(self.yaw))

    def calc_distance(self, point_x, point_y):
        dx = self.rear_x - point_x
        dy = self.rear_y - point_y
        return math.hypot(dx, dy)


class States:

    def __init__(self):
        self.x = []
        self.y = []
        self.yaw = []
        self.v = []
        self.t = []

    def append(self, t, state):
        self.x.append(state.x)
        self.y.append(state.y)
        self.yaw.append(state.yaw)
        self.v.append(state.v)
        self.t.append(t)


def proportional_control(target, current):
    a = Kp * (target - current)

    return a


class TargetCourse:

    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.old_nearest_point_index = None

    def search_target_index(self, state):

        # To speed up nearest point search, doing it at only first time.
        if self.old_nearest_point_index is None:
            # search nearest point index
            dx = [state.rear_x - icx for icx in self.cx]
            dy = [state.rear_y - icy for icy in self.cy]
            d = np.hypot(dx, dy)
            ind = np.argmin(d)
            self.old_nearest_point_index = ind
        else:
            ind = self.old_nearest_point_index
            distance_this_index = state.calc_distance(self.cx[ind],
                                                      self.cy[ind])
            while ind+1 < len(self.cx):
                distance_next_index = state.calc_distance(self.cx[ind + 1],self.cy[ind + 1])
                if distance_this_index < distance_next_index:
                    break
                ind = ind + 1 if (ind + 1) < len(self.cx) else ind
                distance_this_index = distance_next_index
            self.old_nearest_point_index = ind

        Lf = k * state.v + Lfc  # update look ahead distance

        # search look ahead target point index
        while Lf > state.calc_distance(self.cx[ind], self.cy[ind]):
            if (ind + 1) >= len(self.cx):
                break  # not exceed goal
            ind += 1

        return ind, Lf


def pure_pursuit_steer_control(state, trajectory, pind):
    ind, Lf = trajectory.search_target_index(state)

    if pind >= ind:
        ind = pind

    if ind < len(trajectory.cx):
        tx = trajectory.cx[ind]
        ty = trajectory.cy[ind]
    else:  # toward goal
        tx = trajectory.cx[-1]
        ty = trajectory.cy[-1]
        ind = len(trajectory.cx) - 1

    alpha = math.atan2(ty - state.rear_y, tx - state.rear_x) - state.yaw
    

    delta = math.atan2(2.0 * WB * math.sin(alpha) / Lf, 1.0)

    return alpha, delta, ind







FLAG = "PATH"








left_velocity=0.0
right_velocity = 0.0


def mapi( x, in_min,in_max,  out_min, out_max):
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def Wheels(left,right):
    left = constrain(left,-6.28,6.28)
    right = constrain(right,-6.28,6.28)
    print("Left:{} Right:{}".format(left,right))
   
    

  
   

    
def act():
    print("Left:{} Right:{}".format(left_velocity,right_velocity))
    Wheels(left_velocity,right_velocity)  

def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))
    


# Wheels(0,0)

DEGTORAD = 0.0174532925199432957
RADTODEG = 57.295779513082320876





def get_bearing_in_degrees():
    # north = cm.getValues()
    # rad = math.atan2(north[0], north[2])
    # bearing = (rad - 1.5708) / math.pi * 180.0
    # if (bearing < 0.0):
    #     bearing = bearing + 360.0

    # return bearing
    return 0
    

def geoDistance(a, b):
   R = 1000
   p1 = a[0] * DEGTORAD
   p2 = b[0] * DEGTORAD
   dp = (b[0]-a[0]) * DEGTORAD
   dl = (b[2]-a[2]) * DEGTORAD
   x = math.sin(dp/2) * math.sin(dp/2) + math.cos(p1) * math.cos(p2) * math.sin(dl/2) * math.sin(dl/2)
   y = 2 * math.atan2(math.sqrt(x), math.sqrt(1-x))
   return  y * R


def geoBearing(a, b):
   y = math.sin(b[2]-a[2]) * math.cos(b[0])
   x = (math.cos(a[0])*math.sin(b[0]) )- (math.sin(a[0]) * math.cos(b[0])* math.cos(b[2]-a[2]))
   return math.atan2(y, x) * RADTODEG

robotInitialLocation = [10.935963, 0,78.686615]

initialOrientation = get_bearing_in_degrees() * DEGTORAD
cx=[]
cy=[]
# if FLAG == "PATH":
path=[]
path.append(robotInitialLocation)
path.append([10.936080, 0,78.686124])
path.append([10.936584, 0,78.685885])
path.append([10.936849,0, 78.685765])
path.append([10.937285,0, 78.685709])
path.append([10.93769375549963,0, 78.68631176363178])

cx = [x for x,y,z in path]

cy = [z for x,y,z in path]

# if FLAG == "SPIRAL":
    

#     for theta in np.linspace(0,5*3.14):
#         r = ((theta))
#         cx.append(r*math.cos(theta))
#         cy.append(r*math.sin(theta))
        # print(cx)
        # print(cy)
    
# path.append([6.17,0,-10.97])

robotCurrentPose = [robotInitialLocation, initialOrientation]


state = State(x=robotInitialLocation[0], y=robotInitialLocation[2], yaw=0.0, v=0.0)

lastIndex = len(cx) - 1
time2 = 0.0
states = States()
states.append(time2, state)
target_speed = 6.28
target_course = TargetCourse(cx, cy)
target_ind, _ = target_course.search_target_index(state)
# print(target_ind)

def plot_arrow(x, y, yaw, length=0.1, width=0.1, fc="r", ec="k"):
    """
    Plot arrow
    """

    if not isinstance(x, float):
        for ix, iy, iyaw in zip(x, y, yaw):
            plot_arrow(ix, iy, iyaw)
    else:
        plt.arrow(x, y, length * math.cos(yaw), length * math.sin(yaw),
                  fc=fc, ec=ec, head_width=width, head_length=width)
        plt.plot(x, y)

position = robotInitialLocation

left_velocity = 6.28
right_velocity = 6.28

# def turnToGoal(ai,di):
    # turn = di*RADTODEG
    # turn = (gps.getValues()[2]-di)**2
    # print(turn)
    # global left_velocity , target_ind
    # global right_velocity
    
    # while turn > 0.0001 or turn < -0.0001 :
        # print("loop :",turn)
        # robot.step(timestep)
        # if turn > 0:
          # left_velocity += 0.1
          # right_velocity -=0.1
          # Wheels(left_velocity,right_velocity)
          
    
        # if turn < 0:
          # left_velocity -= 0.1
          # right_velocity += 0.1
          # Wheels(left_velocity,right_velocity)
          
        # left_velocity = 0
        # right_velocity =0

        
# def update():

# print(cx,cy)
# hi=0
# while hi<=5:
    # hi=hi+1

    # # moveForward()
    # # pb=[1.61312,0.45,-0.432224]
    # position = robotInitialLocation
    
    # # DX = pb[0] - position[0]
    # # DY = pb[2]- position[2]
    # DX = cx[target_ind] - position[0]
    # DY = cy[target_ind]- position[2]
    # radians = math.atan2(DY,DX)
    # degrees = radians * (180 /math.pi)
    # # cmr =cm.getValues()
    # # rad = math.atan2(cmr[0], cmr[2])
    

    # # clear()
    
    # turn = degrees - get_bearing_in_degrees()
    # k = 1
    # print('turn',turn)
    # turn = turn % 360
    # turn =  turn * DEGTORAD
    # turn = -turn


    # print("rad :",turn)
    
    # v =  (6.28)
    # # v = 25
  
    # print(v)
    # # left_velocity = v * (math.cos(turn) - k * math.sin(turn)  )
    # # left_velocity =  left_velocity / 0.03
    
    # # right_velocity = v * (math.cos(turn) + k * math.sin(turn)  )
    # # right_velocity =  right_velocity / 0.03
    
    # # Wheels(left_velocity,right_velocity)
    
    
    
    # # decide()
    
    # # while (turn < -180): 
    #     # print("while")
    #     # turn += 360
    # # while (turn >  180):
    #     # print("while1")
    #     # turn -= 360
        

    # print("in whiles "+ str(turn))
    # # distance = geoDistance(position,pb)
    
    
    # ai = proportional_control(target_speed, state.v)
    
    # alpha, di, target_ind = pure_pursuit_steer_control(state, target_course, target_ind)
    # # turnToGoal(ai,di)
    # print("alpha :",alpha)
    # alpha = -alpha        #inverting alpha
    # print("alpha :",alpha)
    # left_velocity = v * (math.cos(alpha) - k * math.sin(alpha)  )

    
    # right_velocity = v * (math.cos(alpha) + k * math.sin(alpha)  )

    # # print(left_velocity,right_velocity)
    
    # # Wheels(left_velocity,right_velocity)
    # state.update(ai, di)  # Control vehicle

    # position = [cx[target_ind],0,cy[target_ind]]

    # state.x = position[0]
    # state.y = position[2]
    # state.yaw = get_bearing_in_degrees() * DEGTORAD

    # print(di*RADTODEG)
    
    # time2 += dt
    # states.append(time2, state)
    
    
    # plt.cla()
         
    # plt.gcf().canvas.mpl_connect(
    #     'key_release_event',
    #     lambda event: [exit(0) if event.key == 'escape' else None])
    # # plot_arrow(state.x, state.y, state.yaw)
    # plt.plot(cx, cy, "-r", label="course")
    # # robotInitialLocation = [cx[target_ind],0,cy[target_ind]]

    # print('cx',cx[target_ind],'cy',cy[target_ind])
    # plt.plot(states.x, states.y, "-d", label="trajectory")
    # plt.plot(cx[target_ind], cy[target_ind], "xg", label="target")
    
    # print(states.x,states.y)
    # plt.axis("equal")
    # plt.grid(True)
    # plt.title("Speed[km/h]:" + str(state.v * 3.6)[:4])
    # # plt.autoscale() 
    # plt.pause(0.001)
    # print(state.yaw)
    # time.sleep(5)
    
    # break
    

      
    
         
    # print(radians)
    # print(degrees)
    # print(get_bearing_in_degrees())
    # print(geoBearing(pb,position))
    # print(geoDistance(pb,position))
 
    
    
    # print("Latitude is: {deg:.8f} deg / {lat}".format(deg=position[0], lat=latitude))
    # print("Longitude is: {deg:.8f} deg / {long}".format(deg=position[1],long=longitude))
    # print("Altitude is: {alt:.8f} [m]".format(alt=position[2]))
    # print("Speed is: {speed:.8f} [m/s]".format(speed=speed))
    

