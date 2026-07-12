#!/usr/bin/env python
import rospy
from geometry_msgs.msg import Twist

def draw_circle():
    # 初始化一个ROS节点
    rospy.init_node('circle_drawer', anonymous=True)
    
    # 创建一个发布者，向'/turtle1/cmd_vel'话题发布Twist消息
    pub = rospy.Publisher('/turtle1/cmd_vel', Twist, queue_size=10)
    
    # 设置循环频率为10Hz
    rate = rospy.Rate(10)
    
    # 创建Twist消息
    move_cmd = Twist()
    
    # 设置线速度和角速度，使乌龟画圈
    move_cmd.linear.x = 0.5  # 线速度（m/s）
    move_cmd.angular.z = 0.5  # 角速度（rad/s）
    
    # 在屏幕上打印提示信息
    rospy.loginfo("Drawing a circle. Press Ctrl+C to stop.")
    
    # 循环发布速度指令
    while not rospy.is_shutdown():
        pub.publish(move_cmd)
        rate.sleep()

if __name__ == '__main__':
    try:
        draw_circle()
    except rospy.ROSInterruptException:
        rospy.loginfo("Circle drawing stopped.")
