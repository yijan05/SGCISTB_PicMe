<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up()
    {
        Schema::table('access_logs', function (Blueprint $table) {
            $table->foreignId('user_id')->constrained()->onDelete('cascade');
            $table->string('evento');
            $table->string('metodo')->default('one_class_svm');
            $table->float('confianza')->nullable();
            $table->string('ip_address')->nullable();
            $table->text('user_agent')->nullable();
        });
    }

    public function down()
    {
        Schema::table('access_logs', function (Blueprint $table) {
            $table->dropColumn(['user_id', 'evento', 'metodo', 'confianza', 'ip_address', 'user_agent']);
        });
    }
};