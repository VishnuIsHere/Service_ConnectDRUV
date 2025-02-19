from django.contrib import admin
from .models import Register,OTP,Profile,Services,Subservices, EmployeeRegistration, ServiceRegistry,ServiceRequest,BookingList,Review,Payment




admin.site.register(Register)
admin.site.register(OTP)
admin.site.register(Profile)

admin.site.register(Services)
admin.site.register(Subservices)
admin.site.register(ServiceRequest)




@admin.register(EmployeeRegistration)
class EmployeeRegistrationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'age', 'phone_number', 'created_at')
    search_fields = ('name', 'phone_number')
    list_filter = ('created_at',)


@admin.register(ServiceRegistry)
class ServiceRegistryAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee', 'service', 'min_price', 'max_price', 'description')
    search_fields = ('employee__name', 'service__title')
    list_filter = ('service',)
    
    
    
    
@admin.register(BookingList)
class BookingListAdmin(admin.ModelAdmin):
    list_display = ('register_name', 'booking_date')

    def register_name(self, obj):
        return obj.register.name if obj.register else "No Register"
    register_name.short_description = "Register Name"



@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service', 'rating', 'created_at')  # Columns shown in admin list view
    list_filter = ('rating', 'created_at')  # Filters for easy sorting
    search_fields = ('user__name', 'service__title', 'comment')  # Searchable fields
    ordering = ('-created_at',)  # Latest reviews appear first
    
    
    
    
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'employee', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_id', 'user__name', 'employee__name']